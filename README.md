# ⚡ PyFlow RPA

> Automação de processos robóticos visual e sem código — construído em Python.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green?logo=qt)
![Selenium](https://img.shields.io/badge/Selenium-4.18%2B-orange?logo=selenium)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-teal?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-purple)
![Blocos](https://img.shields.io/badge/Blocos%20RPA-49-blue)

---

## 📌 O que é o PyFlow RPA?

PyFlow RPA é uma ferramenta desktop de automação visual inspirada no UiPath e no n8n. Você arrasta blocos para um canvas, configura parâmetros e executa fluxos de automação sem escrever uma linha de código.

Os fluxos são salvos como **JSON** e podem ser **exportados como scripts Python standalone** para rodar em qualquer máquina.

---

## 🖥️ Interface & Recursos

- **Canvas visual** com drag & drop de blocos
- **Sub-Processos & Navegação Hierárquica 📦** — Recolha grupos de blocos em um único nó de Subfluxo e "mergulhe" nele com duplo-clique para edição inline com Breadcrumbs.
- **Debugger com Live Watch (Inspeção de Dados) 🐜** — Clique nos "fios" de conexão durante a execução para ver exatamente quais dados (JSON, texto) estão passando entre os blocos.
- **Minimapa de Alta Performance 🗺** — Navegue facilmente por automações gigantes com a visão panorâmica flutuante.
- **Multi-Duplicação Inteligente 📋** — Duplique múltiplos blocos de uma vez mantendo as conexões internas preservadas.
- **Indentação visual automática** — blocos dentro de Se/Loop/Para Cada ficam recuados com borda colorida por escopo.
- **Gatilhos Dinâmicos (Webhooks)** — crie rotas de API personalizadas para disparar fluxos remotamente.
- **Histórico de Execuções e Retomada** — veja logs de falhas e clique em "Retomar" para voltar do bloco exato onde quebrou.
- **Command Palette** `Ctrl+P` estilo VS Code para buscar e adicionar blocos rapidamente.
- **Serviço Daemon (Background)** — rode o servidor de webhooks silenciosamente usando a inicialização do Windows.
- **Gerenciador de assets** para armazenar credenciais e variáveis reutilizáveis.
- **Tema escuro** Catppuccin Mocha com interface premium e animações.

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- Google Chrome instalado
- (opcional) Tesseract OCR instalado para o bloco OCR

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/pyflow-rpa.git
cd pyflow-rpa
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute

```bash
python main.py
```

---

## 📦 Dependências principais

| Biblioteca | Uso |
|---|---|
| `PySide6` | Interface gráfica |
| `selenium` + `webdriver-manager` | Automação web |
| `pyautogui` | Teclado e mouse do sistema |
| `pyperclip` | Clipboard do sistema |
| `requests` | Requisições HTTP |
| `fastapi` + `uvicorn` | API REST local embutida (servidor assíncrono) |
| `openpyxl` | Leitura e escrita de arquivos Excel |
| `pytesseract` + `Pillow` | OCR (extração de texto de imagens) |
| `paramiko` | Transferência SFTP |
| `plyer` | Notificações desktop |
| `schedule` | Agendamento de execuções |

---

## 🧩 Blocos disponíveis (49)

### 🌐 Navegador (21)
| Bloco | O que faz |
|---|---|
| Abrir Navegador | Abre o Chrome em uma URL |
| Clicar em Elemento | Clica em um elemento pelo seletor CSS |
| Preencher Campo | Digita texto em um campo |
| Extrair Texto | Captura o texto de um elemento → variável |
| Extrair Lista | Captura múltiplos elementos → lista |
| Espera Inteligente | Aguarda condição: elemento, URL, texto, carregamento |
| Executar JavaScript | Executa JS via `driver.execute_script()` |
| Smart Click | Clique com fallback para múltiplos seletores |
| Pressionar Tecla | Enter, Tab, Escape, F5... |
| Scroll na Página | Rola para topo, rodapé, elemento ou pixels |
| Tirar Screenshot | Captura a página como PNG |
| Obter URL Atual | Captura a URL do navegador → variável |
| Ação de Mouse | Hover, duplo clique, drag & drop |
| Navegar para URL | Vai para outra URL sem abrir nova janela |
| Voltar / Avançar / Atualizar | Navegação do browser |
| Abrir Nova Aba | Abre aba e navega para URL |
| Fechar Aba | Fecha a aba atual |
| Trocar de Aba | Alterna entre abas abertas |
| Fechar Navegador | Encerra o Chrome |

### 🔧 Controle (15)

> **Arquitetura de marcadores** — Loop, Para Cada e Se não exigem mais contar blocos manualmente.
> Basta inserir o bloco de início, os blocos internos e o bloco de fim correspondente.

| Bloco | O que faz |
|---|---|
| Aguardar | Pausa por N segundos |
| Condição (Se) | Verifica uma condição (veja tipos abaixo) |
| Senão (Else) | Ramo alternativo quando a condição for falsa |
| Fim do Se | Marca o encerramento do bloco Se |
| Loop (Repetir) | Repete N vezes os blocos até o "Fim do Loop" |
| Fim do Loop | Marca o encerramento do bloco Loop |
| Para Cada (For Each) | Itera sobre lista; cada item disponível como variável |
| Fim do Para Cada | Marca o encerramento do bloco Para Cada |
| Definir Variável | Cria/modifica variáveis: set, increment, append, now, multiply... |
| Manipular Texto | 14 operações: upper, replace, regex, split, substring... |
| Exibir Mensagem | Caixa de diálogo modal |
| Notificação Desktop | Notificação sem pausar o fluxo |
| Início / Fim de Sequência | Agrupa e colapsa blocos no canvas |
| Subfluxo | Chama outro fluxo JSON dentro do fluxo atual |

#### Tipos de condição disponíveis no bloco **Condição (Se)**

| Tipo | Descrição |
|---|---|
| `element_exists` | Elemento CSS existe na página |
| `element_not_exists` | Elemento CSS não existe na página |
| `variable_equals` | Variável igual ao valor (case-insensitive) |
| `variable_not_equals` | Variável diferente do valor |
| `variable_contains` | Variável contém o texto |
| `variable_not_contains` | Variável não contém o texto |
| `variable_greater` | Variável numérica maior que o valor |
| `variable_less` | Variável numérica menor que o valor |
| `variable_empty` | Variável está vazia |
| `variable_not_empty` | Variável não está vazia |

### 📁 Arquivos (7)
| Bloco | O que faz |
|---|---|
| Ler CSV | Lê coluna de CSV → lista |
| Salvar em TXT | Escreve texto em arquivo .txt |
| Salvar em CSV | Adiciona linha em arquivo CSV |
| Banco de Dados (SQLite) | SELECT, INSERT, UPDATE, DELETE, CREATE TABLE |
| Excel (.xlsx) | Ler célula/coluna/linha/planilha, escrever célula, adicionar linha |
| Compactar / Descompactar (ZIP) | Cria ou extrai arquivos .zip |
| Carregar .env | Lê variáveis de um arquivo `.env` → contexto do fluxo |

### 🔌 Integração (3)
| Bloco | O que faz |
|---|---|
| HTTP Request | GET/POST/PUT/PATCH/DELETE com headers, body e dot notation |
| Enviar E-mail | SMTP via Gmail, Outlook, Yahoo ou custom |
| FTP / SFTP | Upload, download, listar e deletar arquivos remotos |

### 💻 Sistema (4)
| Bloco | O que faz |
|---|---|
| Teclado do Sistema | Digitar, pressionar tecla, atalho via PyAutoGUI |
| Clipboard | Copiar, colar e limpar o clipboard do sistema |
| OCR (Extrair Texto de Imagem) | Extrai texto de imagem local, screenshot ou navegador |
| Hash de Arquivo | Calcula MD5/SHA1/SHA256 de qualquer arquivo |

---

## 🔁 Controle de Fluxo em detalhe

### Como usar o Loop

```
[Loop — 5 vezes]
  [Clicar em Elemento]
  [Aguardar — 1s]
[Fim do Loop]
```

Arraste o bloco **Loop**, configure `times` (número de repetições) e `delay_between` (pausa entre iterações).
Adicione os blocos de ação dentro e finalize com **Fim do Loop**.
Aninhamento de loops é suportado.

### Como usar o Para Cada

```
[Para Cada — items="João, Maria, Carlos" variável="nome"]
  [Preencher Campo — valor: {{nome}}]
[Fim do Para Cada]
```

O bloco **Para Cada** itera sobre uma lista separada por vírgulas.
O item atual fica disponível como `{{nome}}` (ou o nome que você definir) nos blocos internos.

### Como usar o Se / Senão

```
[Se — numero_baixo < 100]
  [Definir Variável — resultado = "Abaixo do limite"]
[Senão]
  [Definir Variável — resultado = "Acima do limite"]
[Fim do Se]
```

O **Senão** é opcional. Sempre feche com **Fim do Se**.
Todas as estruturas podem ser aninhadas livremente.

---

## 🔄 ConditionalRetry — Retry inteligente por categoria de erro

O runner classifica automaticamente os erros e decide se vale tentar novamente:

| Categoria | Padrão | Por quê |
|---|---|---|
| `timeout` | ✅ retry | Lentidão de rede — geralmente resolve |
| `network` | ✅ retry | Conexão instável — geralmente resolve |
| `stale` | ✅ retry | Elemento ficou stale após reload — resolve |
| `notfound` | ❌ sem retry | Elemento ausente — dificilmente resolve |
| `invalid` | ❌ sem retry | Seletor inválido — nunca resolve |
| `custom` | configurável | Palavras-chave definidas pelo usuário |

Configure em **Configurações → Execução** dentro do PyFlow.

---

## 🔑 Assets e Credenciais

O PyFlow possui um gerenciador de assets para armazenar credenciais e valores reutilizáveis com segurança local:

1. Abra com **Ctrl+A** ou clique em **🔑 Assets** na toolbar
2. Cadastre uma chave (ex: `URL_SISTEMA`) e um valor (ex: `https://sistema.com`)
3. Use nos blocos com a sintaxe: `{{ASSET:URL_SISTEMA}}`

---

## 🌐 API REST Local (FastAPI)

O PyFlow sobe um servidor **FastAPI** em background. A porta padrão é `8080`; se estiver ocupada, uma porta livre é escolhida automaticamente.

```bash
# Listar fluxos salvos
GET  /flows

# Executar um fluxo
POST /run
{ "flow": "nome_do_fluxo" }

# Verificar status
GET  /status

# Histórico de execuções
GET  /history

# Parar execução atual
POST /stop

# Dashboard web
GET  /dashboard

# Documentação interativa (Swagger UI)
GET  /docs
```

Clique em **🌐 API** na toolbar e depois em **Abrir Dashboard** para abrir o painel no navegador. Acesse `/docs` para testar os endpoints diretamente via Swagger.

---

## 🐛 Modo Debug

Clique em **🐛 Debug** ou pressione `Ctrl+D` para executar o fluxo passo a passo:

- `Space` → Avança um bloco
- `F5` → Continua sem pausar
- O bloco atual fica destacado no canvas
- O painel de variáveis atualiza em tempo real após cada passo

---

## ⌨️ Atalhos de teclado

| Atalho | Ação |
|---|---|
| `Ctrl+P` | Command Palette — buscar e adicionar blocos |
| `Ctrl+Enter` | Executar fluxo |
| `Ctrl+D` | Modo debug step-by-step |
| `Ctrl+T` | Galeria de templates |
| `Ctrl+A` | Gerenciador de assets |
| `Ctrl+S` | Salvar fluxo |
| `Ctrl+L` | Limpar canvas |
| `Space` | Próximo passo (modo debug) |
| `F5` | Continuar sem pausar (modo debug) |

---

## 📂 Estrutura do projeto

```
pyflow/
├── main.py                        # Entry point
├── requirements.txt
├── assets.json                    # Assets e credenciais locais
│
├── blocks/                        # Blocos de automação
│   ├── base_block.py              # Classe base com validate_params()
│   ├── browser/                   # Selenium — automação web (21 blocos)
│   │   ├── open_browser.py
│   │   ├── click_element.py
│   │   ├── fill_field.py
│   │   ├── extract_text.py        # Também armazena o contexto de variáveis
│   │   ├── extract_list.py
│   │   ├── smart_wait.py
│   │   ├── execute_script.py
│   │   ├── nav_controls.py        # Navigate, GoBack, Forward, Refresh, Tabs...
│   │   └── ...
│   ├── control/                   # Lógica e fluxo (15 blocos)
│   │   ├── if_block.py            # 10 tipos de condição
│   │   ├── else_block.py          # Ramo alternativo do Se
│   │   ├── end_if_block.py        # Marcador de fim do Se
│   │   ├── loop_block.py          # Repetição por contador
│   │   ├── end_loop_block.py      # Marcador de fim do Loop
│   │   ├── for_each_block.py      # Iteração sobre lista
│   │   ├── end_foreach_block.py   # Marcador de fim do Para Cada
│   │   ├── set_variable.py
│   │   ├── text_manipulation.py
│   │   ├── show_message.py
│   │   ├── desktop_notification.py
│   │   ├── subflow_block.py
│   │   ├── sequence_start_block.py
│   │   └── sequence_end_block.py
│   ├── files/                     # CSV, TXT, Excel, SQLite, ZIP, .env (7 blocos)
│   ├── integration/               # HTTP, E-mail, FTP/SFTP (3 blocos)
│   └── system/                    # Teclado, Clipboard, OCR, Hash (4 blocos)
│
├── engine/
│   ├── runner.py                  # Motor de execução: ConditionalRetry + controle de fluxo
│   ├── debug_runner.py            # Motor step-by-step
│   ├── flow_manager.py            # Salvar/carregar fluxos JSON
│   ├── flow_exporter.py           # Exportar fluxo como .py
│   ├── api_server.py              # Servidor FastAPI local (porta auto-detect)
│   ├── asset_manager.py           # Gerenciador de assets
│   └── theme_manager.py           # Tema Catppuccin Mocha (dark only)
│
├── ui/
│   ├── main_window.py             # Janela principal com QSplitter redimensionável
│   ├── canvas.py                  # Canvas drag & drop + indentação visual por escopo
│   ├── block_panel.py             # Painel lateral de blocos por categoria
│   ├── log_panel.py               # Log com filtros, busca e exportação
│   ├── debug_toolbar.py           # Controles do modo debug
│   ├── command_palette.py         # Busca Ctrl+P
│   ├── templates_dialog.py        # Galeria de templates
│   ├── assets_dialog.py           # Gerenciador de assets
│   ├── api_status_dialog.py       # Status da API + botão abrir Dashboard
│   └── ...
│
└── flows/                         # Fluxos salvos (.json)
    ├── template_login_extracao.json
    ├── template_scraping_lista.json
    ├── template_monitor_preco.json
    ├── template_preencher_formulario.json
    ├── template_disparo_api.json
    ├── teste_controle_fluxo.json  # Testa Se, Loop, Para Cada e aninhamento
    └── ...                        # +25 fluxos de teste e exemplo
```

---

## 🔧 Tesseract OCR (opcional)

Para usar o bloco OCR, instale o Tesseract no sistema:

**Windows:**
Baixe o instalador em [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) e marque **Portuguese** durante a instalação.

Adicione ao início do `blocks/system/ocr_block.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-por
```

**Mac:**
```bash
brew install tesseract
```

---

## 🗂️ Fluxos de exemplo incluídos

| Fluxo | O que demonstra |
|---|---|
| `template_login_extracao.json` | Login em site + extração de dados |
| `template_scraping_lista.json` | Scraping de múltiplos itens com Para Cada |
| `template_monitor_preco.json` | Monitoramento de preço com alerta |
| `template_preencher_formulario.json` | Preenchimento de formulário web |
| `template_disparo_api.json` | Chamada de API externa + processamento |
| `teste_controle_fluxo.json` | Loop, Para Cada, Se/Senão e aninhamento completo |
| `teste_conditional_retry.json` | ConditionalRetry por categoria de erro |
| `teste_http_request.json` | GET/POST com dot notation e variáveis |
| `teste_sqlite.json` | CREATE TABLE, INSERT, SELECT com SQLite |
| `teste_excel.json` | Ler e escrever em planilhas .xlsx |
| `teste_subfluxo_pai.json` | Chamada de subfluxo aninhado |
| `teste_text_manipulation.json` | Todas as 14 operações de texto |
| `teste_zip.json` | Compactar e descompactar arquivos |

---

## 📊 Estatísticas do projeto

| Métrica | Valor |
|---|---|
| Arquivos Python | ~135 |
| Blocos RPA | 49 |
| Fluxos de exemplo | 30+ |
| Tipos de condição (Se) | 10 |

---

## ⚠️ Problemas Conhecidos (Issues)

Atualmente as seguintes funcionalidades estão mapeadas para melhorias futuras:
- **PyFlow Daemon (Serviço de Background)**: O script `.vbs` de inicialização automática não possui feedback visual e pode ter problemas em lidar com múltiplas instâncias ou matar os processos do Chrome gerados pelo modo headless de forma limpa.
- **Gravador de Macro**: A ferramenta que tenta transcrever as ações do navegador não é tão precisa. Uma solução nativa como Inspector de XPath para selecionar diretamente nas páginas web será abordada no futuro.

---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

---

<p align="center">Feito com ⚡ Python + PySide6</p>
