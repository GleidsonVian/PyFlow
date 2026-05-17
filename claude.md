# 🤖 Guia de Continuidade do Claude (Guia-Guia) — PyFlow RPA

> Este arquivo é um manifesto e guia de arquitetura criado especificamente para a próxima Inteligência Artificial que assumir o desenvolvimento deste projeto. Ele resume de forma precisa as regras do ecossistema, os upgrades de design premium implementados e as armadilhas comuns que devem ser evitadas.

---

## 📌 1. Visão Geral do Projeto

O **PyFlow RPA** é um estúdio de automação visual desktop (estilo UiPath/n8n) de alto desempenho escrito em **Python 3.11+** com **PySide6 (Qt)**. Os usuários criam robôs de automação visual por meio de blocos de arrastar e soltar (drag & drop), cujos fluxos são serializados em **JSON** e podem ser exportados como scripts Python nativos autônomos.

### Tecnologias-Chave:
*   **Interface Gráfica:** PySide6 (Qt) rodando com DPI Awareness forçado.
*   **Design & Cores:** Tema **Catppuccin Mocha** escuro exclusivo. Não reintroduza temas claros.
*   **Automação Web:** Selenium WebDriver + ChromeDriver (com gerenciamento dinâmico headless via interface).
*   **Servidor Local & Webhooks:** FastAPI + Uvicorn rodando assincronamente em porta auto-detectável (padrão: `8080`).

---

## 🎨 2. Arquitetura Premium do Painel Direito (Refatorado)

**O painel direito foi completamente redesenhado para eliminar o aninhamento duplo de abas.**
Anteriormente, o painel de propriedades (`PropertiesPanel`) possuía um `QTabWidget` interno que criava duas fileiras de abas concorrentes. Essa redundância foi removida.

### A Estrutura Unificada de Abas (`ui/main_window.py`):
O painel lateral agora contém apenas **um** `QTabWidget` de fileira única de alta visibilidade, distribuído da seguinte forma:
1.  **`⚙ Props` (`ui/properties_panel.py`):** Formulário vertical limpo e inteligente para edição de parâmetros do nó selecionado. Não possui abas internas.
2.  **`👁 Preview` (`ui/preview_panel.py`):** Nosso painel especializado standalone para validação rápida. Ele contém:
    *   *Element Tester:* Verifica seletores CSS no navegador Chrome ativo e retorna feedback colorido instantâneo (Verde para elemento único, Amarelo para múltiplos seletores, Vermelho para ausente).
    *   *Context Watcher:* Mostra o valor atual de variáveis extraídas pelo robô.
    *   *Screenshot Preview:* Exibe as imagens capturadas por blocos de Screenshot de forma responsiva.
    *   *URL Watcher:* Exibe a página ativa no navegador do robô.
3.  **`𝑥 Vars` (`ui/variables_panel.py`):** Gerencia variáveis de contexto e Assets locais em tempo real.
4.  **`📜 Logs` (`ui/log_panel.py`):** Histórico de execução em tempo real do runner com suporte a busca e filtros.
5.  **`❓ Ajuda` (`ui/help_panel.py`):** Central de documentação markdown e atalhos rápidos do PyFlow.

---

## 🔀 3. Mapeador de Dados Visual (Visual Data Mapper)

Para facilitar a passagem de variáveis complexas e objetos JSON sem exigir sintaxe manual complexa do usuário, implementamos um mapeador visual na janela de edição de detalhes de blocos (`NodeDetailsDialog` em `ui/node_details_dialog.py`):

### Como funciona:
*   **Árvore de Variáveis (`DraggableTreeWidget`):** Exibe chaves e dicionários disponíveis no fluxo com emojis temáticos (📦, 📂, 🔤).
*   **Efeito Arrastar & Soltar (Drag & Drop):** Ao arrastar uma chave, é criada uma pílula flutuante estilizada em tom Mauve Catppuccin (`#cba6f7`) com bordas arredondadas e texto em negrito que segue o cursor.
*   **Inputs Inteligentes (`MappableLineEdit` e `MappableTextEdit`):**
    *   Possuem uma animação de foco visual que brilha em lilás (`2px solid #cba6f7`) quando uma variável passa por cima deles.
    *   Ao soltar a pílula, o token `{{nome_variavel}}` é inserido de forma cirúrgica na coordenada exata onde o cursor do mouse foi solto.
*   **Double-Click Veloz:** O usuário pode dar duplo-clique em qualquer item na árvore de variáveis para inseri-lo diretamente no último campo de texto focado.

---

## 🔧 4. Controle de Fluxo & Motor de Execução (Runner)

### Regra de Ouro do Escopo (SEMPRE siga esta regra):
> [!IMPORTANT]
> Os blocos de escopo como **Loop (Repetir)**, **Para Cada (For Each)** e **Condição (Se)** **NÃO utilizam** e **NUNCA devem utilizar** o parâmetro `blocks_count`. A contagem manual de blocos foi totalmente abolida.

*   **Padrão de Marcadores:** O motor usa blocos de início e marcadores de fim (`EndLoopBlock`, `EndForEachBlock`, `EndIfBlock`).
*   **Desvio de Fluxo:** O motor de execução (`engine/runner.py`) detecta chaves de retorno do execute (`loop`, `foreach`, `if_result`), localiza o marcador de encerramento usando a função `_find_scope_end()` e despacha a execução dos blocos internos via `_run_sub()`.
*   **Aninhamento Perfeito:** `_run_sub()` chama diretamente `self.run(steps)`. Isso ativa a recursão natural do motor de execução, garantindo que loops e condições aninhadas em qualquer nível funcionem com 100% de precisão.

---

## 🔐 5. Fonte da Verdade para Variáveis

Toda a manipulação de memória e resolução de tokens passa pelo arquivo centralizador:
*   **Caminho:** [execution_context.py](file:///c:/Users/Gleidson/pasta4/Python/pyflow/pyflow/engine/execution_context.py)
*   **Fail-Fast (ValueError):** Ao resolver parâmetros com `resolve_params()`, se o token `{{variavel}}` ou uma dot-notation `{{objeto.propriedade}}` referenciar uma chave que não existe no dicionário, o motor dispara imediatamente um `ValueError` fatal para interromper o fluxo e evitar automações rodando com dados nulos ou incorretos.

---

## 🎹 6. Atalhos & Facilidades Globais

| Atalho | Ação |
|---|---|
| **`Ctrl+Shift+L`** | **Auto-Organizar Canvas** — Redimensiona e alinha perfeitamente todos os blocos do canvas via algoritmo `canvas.auto_layout`. |
| **`Ctrl+P`** | **Command Palette** — Busca e insere blocos na tela no ponto do cursor. |
| **`Ctrl+Enter`** | **Executar** — Inicia a execução do fluxo de automação. |
| **`Ctrl+D`** | **Depuração** — Inicia o executor em modo debug step-by-step (`Space` avança, `F5` continua). |
| **`Ctrl+A`** | **Assets** — Gerenciador de credenciais seguras. |

---

## 🛠️ 7. Novos Blocos Adicionados e Robustez

*   **`ReadPDFBlock` (blocks/files/read_pdf.py):** Extração de texto de PDFs utilizando a biblioteca `pdfplumber` de forma nativa.
*   **`TextToSpeechBlock` (blocks/system/text_to_speech.py):** Criação de audiolivros ou alertas em áudio MP3 a partir de texto utilizando a biblioteca `gTTS` com seletor de idiomas (`pt`, `en`, `es`, `fr`).
*   **Instalação Automática:** O arquivo [main.py](file:///c:/Users/Gleidson/pasta4/Python/pyflow/pyflow/main.py) possui um sistema inteligente de startup que verifica o `requirements.txt` e instala automaticamente dependências ausentes de forma transparente para o usuário final.
*   **Resiliência no FileManager:** Escritas de arquivos que costumavam disparar permissões negadas no Windows (`WinError 32`) agora rodam sob uma rotina de retentativas inteligentes com delay de segurança.

---

## 📝 8. Diretrizes de Desenvolvimento para a Próxima IA

Se você é o assistente que dará continuidade a este código:
1.  **Respeite o Design Catppuccin Mocha:** Use sempre a paleta de cores fornecida em `theme_manager.py` (Mauve `#cba6f7`, Sapphire `#74c7ec`, Lavender `#b4befe`, Mantle `#181825`, etc.).
2.  **Crie Sempre Fluxos de Teste:** Toda funcionalidade nova ou bloco novo deve acompanhar um arquivo JSON de teste com prefixo `flows/teste_<funcionalidade>.json`.
3.  **Não Reintroduza Abas Aninhadas:** Mantenha o painel da direita limpo com a fileira de 5 abas unificadas. Se criar novos tipos de validação visual, insira-os como sub-widgets da aba `Preview` (`ui/preview_panel.py`).
4.  **Pergunte ao Dono do Projeto (Gleidson):** Se houver alguma ambiguidade sobre a arquitetura ou sobre qual arquivo ler, prefira pedir confirmação no chat antes de fazer alterações invasivas.

---

*Handoff document para continuidade de desenvolvimento — PyFlow RPA. Criado com dedicação.*
