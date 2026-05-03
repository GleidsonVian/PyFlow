# ⚡ PyFlow RPA

> Automação de processos robóticos visual e sem código — construído em Python.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green?logo=qt)
![Selenium](https://img.shields.io/badge/Selenium-4.18%2B-orange?logo=selenium)
![License](https://img.shields.io/badge/License-MIT-purple)
![Blocos](https://img.shields.io/badge/Blocos%20RPA-44-blue)

---

## 📌 O que é o PyFlow RPA?

PyFlow RPA é uma ferramenta desktop de automação visual inspirada no UiPath e no n8n. Você arrasta blocos para um canvas, configura parâmetros e executa fluxos de automação sem escrever uma linha de código.

Os fluxos são salvos como **JSON** e podem ser **exportados como scripts Python standalone** para rodar em qualquer máquina.

---

## 🖥️ Interface

- **Canvas visual** com drag & drop de blocos
- **Debug step-by-step** com destaque do bloco atual e painel de variáveis ao vivo
- **Command Palette** `Ctrl+P` estilo VS Code para buscar e adicionar blocos rapidamente
- **Galeria de templates** prontos para começar
- **Log panel** com filtros por tipo, busca em tempo real, copiar e exportar como `.txt`
- **Agendador** integrado para executar fluxos em horários específicos
- **API REST local** em `http://localhost:8080` para integrar com sistemas externos
- **Gerenciador de assets** para armazenar credenciais e variáveis reutilizáveis
- **Modo escuro** com tema Catppuccin

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
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
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
| `flask` | API REST local embutida |
| `openpyxl` | Leitura e escrita de arquivos Excel |
| `pytesseract` + `Pillow` | OCR (extração de texto de imagens) |
| `paramiko` | Transferência SFTP |
| `plyer` | Notificações desktop |
| `schedule` | Agendamento de execuções |

---

## 🧩 Blocos disponíveis (44)

### 🌐 Navegador (22)
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
| Fechar Aba / Trocar de Aba | Gerenciamento de abas |
| Fechar Navegador | Encerra o Chrome |

### 🔧 Controle (10)
| Bloco | O que faz |
|---|---|
| Aguardar | Pausa por N segundos |
| Condição (If) | Verifica condição e pula blocos |
| Loop (Repetir) | Repete N vezes um grupo de blocos |
| Para Cada (For Each) | Itera sobre lista |
| Definir Variável | Cria/modifica variáveis: set, increment, append, now, multiply... |
| Manipular Texto | 14 operações: upper, replace, regex, split, substring... |
| Exibir Mensagem | Caixa de diálogo modal |
| Notificação Desktop | Notificação sem pausar o fluxo |
| Início / Fim de Sequência | Agrupa e colapsa blocos no canvas |
| Subfluxo | Chama outro fluxo JSON dentro do fluxo atual |

### 📁 Arquivos (5)
| Bloco | O que faz |
|---|---|
| Ler CSV | Lê coluna de CSV → lista |
| Salvar em TXT | Escreve texto em arquivo .txt |
| Salvar em CSV | Adiciona linha em arquivo CSV |
| Banco de Dados (SQLite) | SELECT, INSERT, UPDATE, DELETE, CREATE TABLE |
| Excel (.xlsx) | Ler célula/coluna/linha/planilha, escrever célula, adicionar linha |

### 🔌 Integração (3)
| Bloco | O que faz |
|---|---|
| HTTP Request | GET/POST/PUT/PATCH/DELETE com headers, body e dot notation |
| Enviar E-mail | SMTP via Gmail, Outlook, Yahoo ou custom |
| FTP / SFTP | Upload, download, listar e deletar arquivos remotos |

### 💻 Sistema (3)
| Bloco | O que faz |
|---|---|
| Teclado do Sistema | Digitar, pressionar tecla, atalho via PyAutoGUI |
| Clipboard | Copiar, colar e limpar o clipboard do sistema |
| OCR (Extrair Texto de Imagem) | Extrai texto de imagem local, screenshot ou navegador |

---

## 🔑 Assets e Credenciais

O PyFlow possui um gerenciador de assets para armazenar credenciais e valores reutilizáveis com segurança local:

1. Abra com **Ctrl+A** ou clique em **🔑 Assets** na toolbar
2. Cadastre uma chave (ex: `URL_SISTEMA`) e um valor (ex: `https://sistema.com`)
3. Use nos blocos com a sintaxe: `{{ASSET:URL_SISTEMA}}`

---

## 🌐 API REST Local

O PyFlow sobe um servidor Flask em background em `http://127.0.0.1:8080`:

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
```

Clique em **🌐 API** na toolbar para ver a documentação interativa com exemplos prontos.

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
├── main.py                    # Entry point
├── requirements.txt
├── assets.json                # Assets e credenciais locais
│
├── blocks/                    # Blocos de automação
│   ├── browser/               # Selenium — automação web
│   ├── control/               # Lógica e fluxo
│   ├── files/                 # CSV, TXT, Excel, SQLite
│   ├── integration/           # HTTP, E-mail, FTP/SFTP
│   └── system/                # Teclado, Clipboard, OCR
│
├── engine/
│   ├── runner.py              # Motor de execução com retry
│   ├── debug_runner.py        # Motor step-by-step
│   ├── flow_manager.py        # Salvar/carregar fluxos JSON
│   ├── flow_exporter.py       # Exportar fluxo como .py
│   ├── api_server.py          # API REST Flask local
│   └── asset_manager.py       # Gerenciador de assets
│
├── ui/
│   ├── main_window.py         # Janela principal
│   ├── canvas.py              # Canvas drag & drop
│   ├── block_panel.py         # Painel de blocos
│   ├── log_panel.py           # Log com filtros
│   ├── debug_toolbar.py       # Controles do modo debug
│   ├── command_palette.py     # Busca Ctrl+P
│   ├── templates_dialog.py    # Galeria de templates
│   ├── assets_dialog.py       # Gerenciador de assets
│   └── ...
│
└── flows/                     # Fluxos salvos (.json)
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

## 📊 Estatísticas do projeto

| Métrica | Valor |
|---|---|
| Arquivos Python | 128 |
| Linhas de código | 20.715 |
| Blocos RPA | 44 |
| Fluxos de exemplo | 75 |

---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

---

<p align="center">Feito com ⚡ Python + PySide6</p>
