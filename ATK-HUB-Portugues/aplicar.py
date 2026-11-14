"""Instalador offline de pt-BR para o ATK HUB. Nao altera perfis ou firmware."""
import argparse
import base64
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TARGET = Path(r'C:\Program Files\ATK HUB\resources\main\app.asar')
CONFIG = json.loads((HERE / 'compatibilidade.json').read_text(encoding='utf-8'))
ORIGINAL_HASH = CONFIG['archive_sha256']
BACKUP = TARGET.with_name('app.asar.original-' + ORIGINAL_HASH[:12] + '.bak')
MARKER = '/* ATK-HUB-pt-BR-local-v1 */'
ATK_EXE = TARGET.parents[2] / 'ATK HUB.exe'
NO_WINDOW = 0x08000000

PROCESS_QUERY = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$session = [System.Diagnostics.Process]::GetCurrentProcess().SessionId
$items = @(Get-CimInstance Win32_Process -Filter "Name = 'ATK HUB.exe'" |
    Where-Object { $_.SessionId -eq $session } |
    ForEach-Object { [pscustomobject]@{
        id = [int]$_.ProcessId
        parent_id = [int]$_.ParentProcessId
        executable = $_.ExecutablePath
    } })
ConvertTo-Json -InputObject $items -Compress
'''

def powershell(script, **environment):
    env = os.environ.copy()
    env.update(environment)
    command = Path(env.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    script = "$ProgressPreference = 'SilentlyContinue';\n" + script
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    return subprocess.run(
        [str(command), '-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        env=env, capture_output=True, text=True, encoding='utf-8', errors='replace',
        creationflags=NO_WINDOW, timeout=30, check=True,
    )

def running_atk_pids(tracked=()):
    processes = json.loads(powershell(PROCESS_QUERY).stdout.strip() or '[]')
    expected = os.path.normcase(str(ATK_EXE.resolve()))
    selected = {
        int(item['id']) for item in processes
        if item.get('executable') and os.path.normcase(item['executable']) == expected
    }
    # Electron children can hide their path; only include those linked to this installation.
    selected.update(int(item['id']) for item in processes
                    if not item.get('executable') and int(item['id']) in tracked)
    changed = True
    while changed:
        changed = False
        for item in processes:
            pid, parent = int(item['id']), int(item['parent_id'])
            if item.get('executable') and os.path.normcase(item['executable']) != expected:
                continue
            if parent in selected and pid not in selected:
                selected.add(pid)
                changed = True
            if pid in selected:
                for ancestor in processes:
                    if int(ancestor['id']) == parent and not ancestor.get('executable') and parent not in selected:
                        selected.add(parent)
                        changed = True
    if processes and not selected and not any(item.get('executable') for item in processes):
        raise ValueError('Nao foi possivel identificar o ATK HUB. Execute o instalador como administrador.')
    return sorted(selected)

def wait_for_atk_exit(tracked, seconds):
    deadline = time.monotonic() + seconds
    while True:
        remaining = running_atk_pids(tracked)
        if not remaining or time.monotonic() >= deadline:
            return remaining
        tracked.update(remaining)
        time.sleep(0.3)

def close_atk(pids):
    if not pids:
        return
    print('Fechando o ATK HUB automaticamente...')
    powershell(r'''
$ErrorActionPreference = 'Stop'
foreach ($processId in ($env:ATK_PTBR_PIDS -split ',')) {
    $process = Get-Process -Id ([int]$processId) -ErrorAction SilentlyContinue
    if ($process) { [void]$process.CloseMainWindow() }
}
''', ATK_PTBR_PIDS=','.join(str(pid) for pid in pids))
    tracked = set(pids)
    remaining = wait_for_atk_exit(tracked, 4)
    if remaining:
        # Closing a window may only send ATK to its tray. End only the identified app processes.
        command = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/taskkill.exe'
        for pid in remaining:
            subprocess.run([str(command), '/PID', str(pid), '/F'], capture_output=True,
                           creationflags=NO_WINDOW, timeout=15)
        remaining = wait_for_atk_exit(tracked, 5)
    if remaining:
        raise ValueError('Nao foi possivel encerrar o ATK HUB automaticamente. A traducao nao foi aplicada.')

def reopen_atk():
    if running_atk_pids():
        return
    print('Reabrindo o ATK HUB...')
    # Ask the desktop shell to launch it in the interactive user's session.
    powershell(r'''
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$shell.ShellExecute($env:ATK_PTBR_EXE, '', $env:ATK_PTBR_DIR, 'open', 1)
''', ATK_PTBR_EXE=str(ATK_EXE), ATK_PTBR_DIR=str(ATK_EXE.parent))
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if running_atk_pids():
            return
        time.sleep(0.3)
    raise ValueError('O arquivo foi processado, mas o ATK HUB nao reabriu. Abra-o pelo atalho habitual.')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def update_hint():
    repository = CONFIG.get('repository_url', '').rstrip('/')
    return '\nPacote atualizado: ' + repository + '/releases/latest' if repository else ''

def files(directory, prefix=''):
    for name, info in directory.get('files', {}).items():
        path = prefix + name
        if 'files' in info:
            yield from files(info, path + '/')
        else:
            yield path, info

def read_asar(data):
    if len(data) < 16:
        raise ValueError('Arquivo ASAR incompleto.')
    first, header_size, payload_size, string_size = struct.unpack('<4I', data[:16])
    if first != 4 or header_size != payload_size + 4 or string_size > header_size:
        raise ValueError('Cabecalho ASAR desconhecido.')
    header = json.loads(data[16:16 + string_size])
    base = 8 + header_size
    return header, base

def patched_script(source):
    if MARKER in source:
        raise ValueError('O portugues ja esta instalado.')
    replacements = [
        (CONFIG['locale_map'] + '={', CONFIG['locale_map'] + '={pt:"pt-BR","pt-BR":"pt-BR","pt-PT":"pt-BR",'),
        ('{label:"English",value:"en-us"}', '{label:"English",value:"en-us"},{label:"Português (Brasil)",value:"pt-BR"}'),
    ]
    dictionary = json.loads((HERE / 'pt-BR.json').read_text(encoding='utf-8'))
    original = '"../../packages/atk-i18n/locales/pt-BR.json":' + CONFIG['pt_module']
    payload = '{default:' + json.dumps(dictionary, ensure_ascii=True, separators=(',', ':')) + '}'
    if CONFIG.get('locale_loading') == 'async':
        payload = '()=>Promise.resolve(' + payload + ')'
    replacement = '"../../packages/atk-i18n/locales/pt-BR.json":' + payload
    replacements.append((original, replacement))
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Esta versao do ATK HUB e diferente da versao validada. Nada foi instalado.')
        source = source.replace(old, new, 1)
    return MARKER + '\n' + source

def build(original):
    if sha(original) != ORIGINAL_HASH:
        raise ValueError('O ATK HUB foi atualizado novamente. Este instalador nao corresponde a versao atual.' + update_hint())
    header, base = read_asar(original)
    header = copy.deepcopy(header)
    payload = bytearray()
    renderer = CONFIG['renderer_path']
    replaced = 0
    for path, info in files(header):
        if 'offset' not in info or info.get('unpacked'):
            continue
        start = base + int(info['offset'])
        content = original[start:start + info['size']]
        if len(content) != info['size']:
            raise ValueError('Arquivo ASAR truncado: ' + path)
        if path == renderer:
            content = patched_script(content.decode('utf-8')).encode('utf-8')
            replaced += 1
            if 'integrity' in info:
                integrity = info['integrity']
                if integrity.get('algorithm') != 'SHA256':
                    raise ValueError('Algoritmo de integridade desconhecido.')
                block_size = integrity.get('blockSize', 4194304)
                integrity['hash'] = sha(content)
                integrity['blocks'] = [sha(content[i:i + block_size]) for i in range(0, len(content), block_size)]
        info['offset'] = str(len(payload))
        info['size'] = len(content)
        payload.extend(content)
    if replaced != 1:
        raise ValueError('Nao foi encontrado o modulo de idioma esperado.')
    raw_header = json.dumps(header, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    padded = raw_header + b'\x00' * ((-len(raw_header)) % 4)
    header_payload = struct.pack('<I', len(raw_header)) + padded
    header_pickle = struct.pack('<I', len(header_payload)) + header_payload
    result = struct.pack('<II', 4, len(header_pickle)) + header_pickle + payload
    # Every original resource except the language module must remain identical.
    new_header, new_base = read_asar(result)
    old_files = dict(files(read_asar(original)[0]))
    for path, info in files(new_header):
        if 'offset' not in info or info.get('unpacked'):
            continue
        content = result[new_base + int(info['offset']):new_base + int(info['offset']) + info['size']]
        if path != renderer:
            previous = old_files[path]
            old_content = original[base + int(previous['offset']):base + int(previous['offset']) + previous['size']]
            if content != old_content:
                raise ValueError('Recurso inesperadamente alterado: ' + path)
    return bytes(result)

def require_admin():
    if os.name != 'nt':
        raise ValueError('Este instalador deve ser executado no Windows.')
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError('Clique com o botao direito em Instalar-portugues.cmd e escolha Executar como administrador.')

def install_prepared(current_hash, result, restore):
    if running_atk_pids():
        raise ValueError('O ATK HUB foi aberto durante a preparacao. Nada foi alterado; execute o instalador novamente.')
    if sha(TARGET.read_bytes()) != current_hash:
        raise ValueError('O arquivo mudou durante a preparacao. O atualizador pode estar em execucao; tente novamente.')
    if not restore:
        if BACKUP.exists():
            if sha(BACKUP.read_bytes()) != ORIGINAL_HASH:
                raise ValueError('Ja existe um backup diferente. Nada foi alterado.')
        else:
            shutil.copy2(TARGET, BACKUP)
        if sha(BACKUP.read_bytes()) != ORIGINAL_HASH:
            raise ValueError('Nao foi possivel validar o backup original. Nada foi alterado.')
    temporary = TARGET.with_name('app.asar.pt-br.new')
    created = False
    try:
        with temporary.open('xb') as file:
            created = True
            file.write(result)
            file.flush()
            os.fsync(file.fileno())
        if sha(temporary.read_bytes()) != sha(result):
            raise ValueError('Falha ao validar o arquivo preparado. A instalacao original nao foi alterada.')
        if sha(TARGET.read_bytes()) != current_hash or running_atk_pids():
            raise ValueError('O aplicativo ou o atualizador iniciou durante a instalacao. Nada foi alterado; tente novamente.')
        os.replace(temporary, TARGET)
    finally:
        if created and temporary.exists():
            temporary.unlink()
    if sha(TARGET.read_bytes()) != sha(result):
        raise ValueError('Falha na verificacao final. O backup original foi preservado.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.preview:
        result = build(TARGET.read_bytes())
        args.preview.write_bytes(result)
        print('Arquivo de teste criado. A instalacao original nao foi alterada.')
        return
    if not (args.apply or args.restore or args.preview) and getattr(sys, 'frozen', False):
        args.apply = True
    if args.apply == args.restore:
        raise ValueError('Escolha --apply ou --restore.')
    require_admin()
    # Compatibility and all patch preparation happen before closing a running app.
    current = TARGET.read_bytes()
    current_hash = sha(current)
    if args.restore:
        if not BACKUP.exists() or sha(BACKUP.read_bytes()) != ORIGINAL_HASH:
            raise ValueError('Backup original valido nao encontrado.')
        if sha(current) != sha(build(BACKUP.read_bytes())):
            raise ValueError('A instalacao mudou depois do patch; o backup nao sera restaurado sobre outra versao.')
        result = BACKUP.read_bytes()
    else:
        if current_hash != ORIGINAL_HASH and BACKUP.exists():
            original_backup = BACKUP.read_bytes()
            if sha(original_backup) == ORIGINAL_HASH and sha(build(original_backup)) == current_hash:
                print('A traducao deste pacote ja esta instalada. O ATK HUB permanece como estava.')
                if update_hint():
                    print(update_hint().strip())
                return
        result = build(current)
        if BACKUP.exists():
            if sha(BACKUP.read_bytes()) != ORIGINAL_HASH:
                raise ValueError('Ja existe um backup diferente. Nada foi alterado.')
    pids = running_atk_pids()
    was_running = bool(pids)
    try:
        if was_running:
            close_atk(pids)
        install_prepared(current_hash, result, args.restore)
    except Exception:
        if was_running:
            try:
                reopen_atk()
            except Exception:
                print('Nao foi possivel reabrir o ATK HUB. Abra-o pelo atalho habitual.')
        raise
    if was_running:
        reopen_atk()
    print('Original restaurado.' if args.restore else 'Pronto! Escolha Portugues (Brasil) em Settings > Language no ATK HUB.')
    print('Backup original: ' + str(BACKUP))
    if update_hint():
        print(update_hint().strip())

if __name__ == '__main__':
    exit_code = 0
    try:
        main()
    except Exception as error:
        print('ERRO: ' + str(error))
        exit_code = 1
    if getattr(sys, 'frozen', False) and sys.stdin is not None and sys.stdin.isatty():
        try:
            input('\nPressione Enter para fechar...')
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(exit_code)
