# ⚡ PyFlow RPA

> Ferramenta visual de automação de processos robóticos (RPA) desenvolvida em Python — inspirada no UiPath, 100% gratuita e open source.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.x-green?logo=qt&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?logo=selenium&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)

---

## 📋 Sobre o projeto

O **PyFlow RPA** permite criar fluxos de automação arrastando blocos visuais para um canvas central, sem escrever código. Configure os parâmetros de cada bloco, conecte-os em sequência e execute — o motor cuida do resto.

### ✨ Principais funcionalidades

- 🖱️ **Interface drag-and-drop** — arraste blocos do painel e solte no canvas
- 🌐 **Automação web** — controle o Chrome com Selenium (clicar, preencher, extrair texto, screenshot...)
- 🔧 **Blocos de controle** — condições (If), loops, retry automático, variáveis dinâmicas
- 📁 **Leitura e escrita de arquivos** — CSV, TXT com suporte a variáveis `{{variavel}}`
- 🔌 **Integração com APIs** — HTTP Request (GET/POST/PUT/PATCH/DELETE) e envio de e-mail SMTP
- ⏰ **Agendador** — execute fluxos em horários definidos, repetidamente ou em dias da semana
- 📋 **Gerenciador de fluxos** — salve, carregue, renomeie e delete fluxos em JSON
- 🐍 **Exportar como Python** — converta qualquer fluxo em script `.py` standalone
- 🎨 **Blocos coloridos por categoria** — navegador (azul), controle (roxo), arquivos (verde)...
- 📖 **Ajuda integrada** — documentação de cada bloco no próprio painel de propriedades
- 🔄 **Duplicar e reordenar** — clique direito para duplicar, arraste para reordenar blocos

---

## 🖥️ Interface

```
┌─────────────────────────────────────────────────────────────┐
│  ⚡ PyFlow RPA    [Fluxos] [Salvar] [🐍 Exportar] [▶ Executar] │
├──────────────┬──────────────────────────────┬───────────────┤
│   BLOCOS     │         CANVAS               │ PROPRIEDADES  │
│              │                              │               │
│ NAVEGADOR    │  1 ┤ Abrir Navegador ├       │ ⚙ Propriedades│
│ • Abrir Nav  │         ↓                    │ ❓ Ajuda       │
│ • Clicar     │  2 ┤ Preencher Campo ├       │               │
│ • Preencher  │         ↓                    │               │
│              │  3 ┤ Extrair Texto   ├       │               │
│ CONTROLE     │         ↓                    │               │
│ • If         │  4 ┤ Salvar em CSV   ├       │               │
│ • Loop       │                              │               │
│ • For Each   ├──────────────────────────────┤               │
│              │  Log de execução             │               │
└──────────────┴──────────────────────────────┴───────────────┘
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Google Chrome instalado (para automação web)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/pyflow-rpa.git
cd pyflow-rpa

# 2. Crie e ative o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o PyFlow RPA
python main.py
```

### requirements.txt

```
PySide6
selenium
webdriver-manager
schedule
pyautogui
plyer
winotify
```

---

## 📦 Gerar executável (.exe)

Para distribuir o PyFlow RPA sem precisar do Python instalado:

```bash
pip install pyinstaller
python build.py
```

O executável será gerado em `dist/PyFlowRPA/PyFlowRPA.exe`. Compacte a pasta em `.zip` para distribuir.

---

## 🧩 Blocos disponíveis

### 🌐 Navegador
| Bloco | Descrição |
|---|---|
| Abrir Navegador | Abre o Chrome em uma URL |
| Clicar em Elemento | Clica por seletor CSS |
| Preencher Campo | Digita texto em um campo |
| Extrair Texto | Extrai texto de elemento → variável |
| Extrair Lista | Extrai lista de elementos → variável lista |
| Pressionar Tecla | Enter, Tab, Escape, F5... |
| Scroll na Página | Rola para topo, fim ou elemento |
| Tirar Screenshot | Salva captura de tela em PNG |
| Obter URL Atual | Captura URL → variável |
| Ação de Mouse | Hover, duplo clique, drag & drop |
| Navegar para URL | Vai para URL sem abrir nova janela |
| Abrir Nova Aba | Abre aba com URL opcional |
| Fechar Aba / Trocar de Aba | Gerencia abas |
| Fechar Navegador | Encerra o Chrome |

### 🔧 Controle
| Bloco | Descrição |
|---|---|
| Aguardar | Pausa N segundos |
| Condição (If) | Pula blocos se condição for falsa |
| Loop (Repetir) | Repete N blocos X vezes |
| Para Cada (For Each) | Itera sobre lista de valores |
| Exibir Mensagem | Diálogo modal com variáveis |
| Notificação Desktop | Toast notification sem pausar |
| Manipular Texto | 14 operações: upper, replace, regex, split... |

### 📁 Arquivos
| Bloco | Descrição |
|---|---|
| Ler CSV | Lê coluna de CSV → lista |
| Salvar em TXT | Grava texto com suporte a variáveis |
| Salvar em CSV | Adiciona linha com timestamp opcional |

### 🔌 Integração
| Bloco | Descrição |
|---|---|
| HTTP Request | GET/POST/PUT/PATCH/DELETE para APIs REST |
| Enviar E-mail | SMTP: Gmail, Outlook, Yahoo ou custom |

### 💻 Sistema
| Bloco | Descrição |
|---|---|
| Teclado do Sistema | Digita texto e atalhos fora do navegador |

---

## 💡 Variáveis dinâmicas

Use `{{nome_variavel}}` em qualquer campo de texto para inserir valores dinâmicos:

```
Bloco 1: Extrair Texto → selector: h1 → variável: titulo
Bloco 2: Salvar em TXT → content: Título encontrado: {{titulo}}
Bloco 3: HTTP Request  → url: https://api.com/search?q={{titulo}}
```

As variáveis disponíveis são exibidas automaticamente no painel de propriedades.

---

## 📁 Estrutura do projeto

```
pyflow-rpa/
├── main.py                     # Entry point
├── build.py                    # Script de build (.exe)
├── map_project.py              # Gera mapa da arquitetura
├── requirements.txt
│
├── blocks/
│   ├── base_block.py           # Classe abstrata BaseBlock
│   ├── browser/                # Blocos de automação web
│   ├── control/                # Blocos de controle de fluxo
│   ├── files/                  # Blocos de leitura/escrita
│   ├── integration/            # HTTP e e-mail
│   └── system/                 # Interação com o SO
│
├── engine/
│   ├── runner.py               # Motor de execução com retry
│   ├── flow_manager.py         # Salvar/carregar fluxos JSON
│   └── flow_exporter.py        # Exportar como script Python
│
├── ui/
│   ├── main_window.py          # Janela principal
│   ├── canvas.py               # Canvas com drag & drop
│   ├── block_panel.py          # Painel de blocos disponíveis
│   ├── properties_panel.py     # Propriedades + Ajuda integrada
│   ├── log_panel.py            # Log de execução em tempo real
│   ├── flow_manager_dialog.py  # Gerenciador de fluxos
│   ├── scheduler_dialog.py     # Agendador de execuções
│   ├── settings_dialog.py      # Configurações (retry, etc)
│   ├── param_dialog.py         # Popup de parâmetros
│   └── block_docs.py           # Documentação inline dos blocos
│
└── flows/                      # Fluxos salvos (.json)
```

---

## 🔄 Formato dos fluxos (JSON)

Os fluxos são salvos em JSON e podem ser editados manualmente:

```json
{
  "flow_name": "meu_fluxo",
  "created_at": "2026-04-30T00:00:00",
  "steps": [
    {
      "block": "OpenBrowserBlock",
      "params": { "url": "https://exemplo.com", "maximized": true }
    },
    {
      "block": "ExtractTextBlock",
      "params": { "selector": "h1", "variable_name": "titulo", "timeout": "10" }
    },
    {
      "block": "SaveTextBlock",
      "params": { "content": "{{titulo}}", "filepath": "saida/resultado.txt" }
    }
  ]
}
```

---

## ⏰ Agendador

O agendador permite executar fluxos automaticamente:

- **Uma vez** — em um horário específico
- **Repetir** — a cada X minutos ou horas
- **Dias da semana** — toda segunda às 08:00, por exemplo

Acesse pelo botão **⏰ Agendar** na toolbar.

---

## ⚙️ Retry automático

Configure o comportamento em caso de falha pelo botão **⚙** na toolbar:

- Número de tentativas (1 a 10)
- Intervalo entre tentativas (0.5 a 60 segundos)
- Continuar ou parar em caso de falha definitiva

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/novo-bloco`
3. Commit suas mudanças: `git commit -m 'Add: bloco XYZ'`
4. Push: `git push origin feature/novo-bloco`
5. Abra um Pull Request

### Criando um novo bloco

Crie um arquivo em `blocks/categoria/meu_bloco.py`:

```python
from blocks.base_block import BaseBlock

class MeuBlocoBlock(BaseBlock):
    name        = "Meu Bloco"
    description = "Descrição do que faz"
    category    = "Categoria"

    params_schema = [
        {"name": "param1", "label": "Parâmetro 1", "type": "str",
         "required": True, "default": "", "placeholder": "Ex: valor"}
    ]

    def execute(self, params: dict) -> dict:
        valor = params.get("param1", "")
        # lógica aqui
        return {"success": True, "message": f"Executado com: {valor}"}
```

Depois registre em `ui/block_panel.py` e `ui/canvas.py` e adicione a documentação em `ui/block_docs.py`.

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## 🙏 Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| [PySide6](https://doc.qt.io/qtforpython/) | Interface gráfica |
| [Selenium](https://selenium.dev) | Automação do navegador |
| [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) | ChromeDriver automático |
| [schedule](https://schedule.readthedocs.io) | Agendamento de tarefas |
| [PyAutoGUI](https://pyautogui.readthedocs.io) | Interação com teclado/mouse do sistema |
| [PyInstaller](https://pyinstaller.org) | Geração do executável |

---

<div align="center">
  Feito com ❤️ em Python
</div>
