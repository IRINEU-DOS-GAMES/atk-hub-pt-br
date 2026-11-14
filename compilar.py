"""Gera o instalador Windows independente, com solicitacao de administrador."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
KIT = ROOT / 'ATK-HUB-Portugues'

if __name__ == '__main__':
    command = [
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--console',
        '--uac-admin', '--noupx', '--name', 'ATK-HUB-Portugues',
        '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build' / 'work'),
        '--specpath', str(ROOT / 'build'),
        '--add-data', str(KIT / 'compatibilidade.json') + ':.',
        '--add-data', str(KIT / 'pt-BR.json') + ':.',
        str(KIT / 'aplicar.py'),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    print('Instalador criado em dist/ATK-HUB-Portugues.exe')
