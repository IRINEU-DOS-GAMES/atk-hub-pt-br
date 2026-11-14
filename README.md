# ATK HUB em português brasileiro

Pacote comunitário para completar a tradução do ATK HUB e adicionar **Português (Brasil)** ao seletor de idiomas. A escolha fica salva pelo próprio aplicativo.

**[Baixar o instalador pronto na Release mais recente](https://github.com/IRINEU-DOS-GAMES/atk-hub-pt-br/releases/latest)** · [Repositório do projeto](https://github.com/IRINEU-DOS-GAMES/atk-hub-pt-br)

Esta pasta é o local fixo do projeto. O arquivo [ATK-HUB-Portugues-atual.zip](ATK-HUB-Portugues-atual.zip) contém a versão atual para compartilhar. Os pacotes anteriores podem ser guardados em [versoes](versoes).

## Compatibilidade atual

| Item | Versão validada |
| --- | --- |
| Pacote preparado em | 13/11/2026 |
| Instalador compilado em | 14/11/2026 |
| APP_VERSION do ATK HUB | 28 |
| CUR_ASAR_VERSION | 83 |
| Textos no catálogo | 4.733 |
| Sistema | Windows |
| Instalação do ATK HUB | `C:\Program Files\ATK HUB` |
| Pacote compilado | Windows 64 bits; não exige Python instalado |

O instalador confere o hash completo do arquivo da instalação. O mesmo número de versão, sozinho, não garante compatibilidade. Se o arquivo for diferente, o pacote recusa a alteração.

## Instalar

Você pode baixar **apenas o EXE** para instalar diretamente. O **ZIP compilado** contém o mesmo EXE, o arquivo para restaurar o original e as instruções; não é preciso baixar ambos.

1. Baixe o EXE na Release ou extraia **todo** o arquivo [ATK-HUB-Portugues-atual.zip](ATK-HUB-Portugues-atual.zip).
2. Abra **ATK-HUB-Portugues.exe** e aceite a confirmação de administrador do Windows. O executável já contém a solicitação de elevação (escudo).
3. Se o ATK HUB estiver aberto, o instalador fecha o aplicativo, aplica a tradução e o reabre automaticamente. Se já estiver fechado, ele permanece fechado.
4. No ATK HUB, selecione **Português (Brasil)** em **Settings → Language**. Se estava fechado, abra-o quando quiser.

A compatibilidade é verificada antes de fechar o aplicativo. O instalador tenta fechar a janela normalmente; se ela apenas minimizar para a bandeja, encerra os processos dessa instalação para liberar o arquivo. O serviço de dispositivos não é encerrado. Se houver uma falha após o fechamento, tenta reabrir o aplicativo que estava em uso.

Não é necessário aplicar uma versão anterior do pacote. O instalador não baixa programas e não pede senha, conta ou chave de API.

## Desfazer

Execute **Restaurar-original.cmd** e aceite a confirmação de administrador. O mesmo fechamento e reabertura automáticos se aplicam à restauração, preservando o estado inicial. O instalador conserva uma cópia do arquivo original e recusa restaurá-la sobre uma versão que tenha sido atualizada depois.

## O que o pacote altera

Altera a lista de idiomas e o catálogo brasileiro em `resources/main/app.asar`. Mantém DPI, macros, perfis e firmware. O pacote não contém o executável nem o arquivo ASAR do ATK HUB.

Foram reaproveitadas traduções já presentes no aplicativo, completadas lacunas e revisados rótulos. Parte dos textos foi traduzida automaticamente. Conteúdo enviado por servidores, extensões externas e palavras dentro de imagens podem manter o idioma original.

## Atualizações do ATK HUB

Uma atualização do aplicativo pode remover a tradução. Nesse caso é necessário analisar a nova versão e gerar outro pacote. Não edite o hash de compatibilidade para forçar um instalador antigo.

Procure a versão atual nas [Releases deste repositório](https://github.com/IRINEU-DOS-GAMES/atk-hub-pt-br/releases/latest). O próprio instalador informa esse endereço quando encontra uma instalação diferente.

Para manter este projeto, atualize os arquivos em `ATK-HUB-Portugues`, publique um novo ZIP com data em `versoes` e substitua `ATK-HUB-Portugues-atual.zip`. Atualize também `versao-atual.json` e a tabela deste documento.

## Validação

O [relatório de validação](ATK-HUB-Portugues/validacao.json) registra testes de sintaxe JavaScript, integridade do ASAR, carregamento assíncrono do idioma, menu, instalação/restauração em cópia e recusa de versões incompatíveis. O fechamento/reabertura foi testado com um processo descartável no Windows, preservando aplicativos de outra pasta; o EXE foi conferido quanto ao manifesto de administrador e aos dados incorporados. Esses testes não equivalem à instalação e conferência visual em todos os computadores.

Projeto não oficial, sem vínculo com a ATK. As marcas e os textos originais pertencem aos respectivos titulares.

## Compilar a partir dos fontes

O ZIP da Release já contém o instalador pronto. Para recompilá-lo no Windows 64 bits, crie um ambiente Python 3, instale `requirements-build.txt` e execute `python compilar.py`. O resultado fica em `dist/ATK-HUB-Portugues.exe`. O [PyInstaller](https://pyinstaller.org/en/stable/usage.html#windows-specific-options) inclui os dados de idioma e o manifesto `requireAdministrator`.

Os scripts de fonte também podem ser usados sem compilar: exigem Python 3 com o inicializador `py` e execução como administrador. Os arquivos `.cmd` usam o EXE quando ele está presente na mesma pasta.
