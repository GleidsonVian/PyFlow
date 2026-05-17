# 🤖 Guia para IA — Continuidade do Projeto PyFlow RPA

> Este documento foi criado para orientar uma IA assistente que vai continuar o desenvolvimento
> do PyFlow RPA a partir do ponto em que outro agente parou.
> Leia tudo antes de fazer qualquer modificação.

---

## 📌 O que é este projeto?

**PyFlow RPA** é uma ferramenta desktop de automação visual (estilo UiPath/n8n) feita em Python.
O usuário arrasta blocos para um canvas, configura parâmetros e executa fluxos de automação
sem escrever código.

- **Interface:** PySide6 (Qt)
- **Automação web:** Selenium + ChromeDriver
- **API local:** FastAPI + Uvicorn (servidor embutido, porta padrão 8080)
- **Fluxos salvos como:** JSON na pasta `flows/` (suporta `_internal_steps` para sub-processos)
- **Execução:** Motor Híbrido (Linear + Grafo via `run_graph`)
- **Tema:** Catppuccin Mocha (dark only)
- **Python:** 3.11+

---

## 🗂️ Mapa dos arquivos mais importantes

### Caminho raiz do projeto
```
C:\Users\Gleidson\pasta4\Python\pyflow\pyflow\
```

---

### 1. `blocks/base_block.py` — A classe que todo bloco herda

**Nunca modifique sem necessidade.** Todos os blocos herdam de `BaseBlock`.

```python
class MeuNovoBloco(BaseBlock):
    name        = "Nome exibido na interface"
    description = "Descrição curta"
    category    = "Controle"   # ou "Navegador", "Arquivos", "Integração", "Sistema"
    params_schema = [
        {
            "name":        "meu_param",
            "label":       "Rótulo visível",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Exemplo de valor"
        }
    ]

    def execute(self, params: dict) -> dict:
        # Sempre comece validando
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        # Sua lógica aqui...

        return {
            "success": True,
            "message": "Mensagem de sucesso",
            "data": {}       # opcional — usado por blocos de controle de fluxo
        }
```

**Retorno obrigatório:** `{"success": bool, "message": str}`.
`"data"` é opcional e só é usado por blocos de controle (Se, Loop, Para Cada).

---

### 2. `ui/block_panel.py` — Painel lateral de blocos (onde o usuário arrasta)

**Modifique sempre que criar um novo bloco.**

Dois lugares para alterar:

**a) Importar a classe:**
```python
from blocks.minha_categoria.meu_bloco import MeuNovoBloco
```

**b) Adicionar em `AVAILABLE_BLOCKS`:**
```python
AVAILABLE_BLOCKS = [
    ...
    MeuNovoBloco,   # adicione na posição correta (por categoria)
    ...
]
```

A ordem em `AVAILABLE_BLOCKS` é a ordem exibida no painel.
As categorias são agrupadas automaticamente pela propriedade `category` do bloco.

---

### 3. `ui/canvas.py` — Canvas visual (onde os blocos ficam depois de arrastados)

**Modifique sempre que criar um novo bloco** para que ele apareça no canvas.

Dois lugares para alterar:

**a) Importar a classe:**
```python
from blocks.minha_categoria.meu_bloco import MeuNovoBloco
```

**b) Adicionar em `BLOCK_REGISTRY`** (dicionário `nome_classe → classe`):
```python
BLOCK_REGISTRY = {
    ...
    "MeuNovoBloco": MeuNovoBloco,
    ...
}
```

**Se o novo bloco for de escopo (abre/fecha um bloco interno, como Loop ou Se):**
Também atualize as constantes no Canvas:
```python
_SCOPE_COLORS = {
    "MeuBlocoDeEscopo": "#cor_hex",   # cor da borda de indentação
}
_OPEN_TYPES  = frozenset({..., "MeuBlocoDeEscopo"})
_CLOSE_TYPES = frozenset({..., "FimDoMeuBloco"})
```

---

### 4. `engine/runner.py` — Motor de execução principal

**Modifique apenas se:**
- O novo bloco tiver lógica de controle de fluxo (loop, condição, etc.)
- Precisar alterar o comportamento de retry
- Precisar alterar como variáveis são resolvidas

**Pontos chave do runner:**

- `_SKIP_TYPES` — frozenset com os tipos que são **marcadores de fim** e devem ser ignorados pelo loop principal:
  ```python
  _SKIP_TYPES = frozenset({"EndLoopBlock", "EndForEachBlock", "EndIfBlock", "ElseBlock"})
  ```
  Se criar um novo bloco de fim (ex: `EndMeuBloco`), adicione aqui.

- `resolve_params()` — substitui `{{variavel}}` e `{{ASSET:chave}}` pelos valores reais antes de executar.

- `_execute_with_retry()` — executa o bloco com ConditionalRetry.

- `run()` — loop principal. Detecta `data["loop"]`, `data["foreach"]`, `data["if_result"]`
  no retorno do bloco e executa sub-fluxos.

- `_run_sub()` — apenas chama `self.run(steps)`. Não mude isso — é o que permite aninhamento correto.

**Se criar um bloco de escopo novo** (ex: TryCatch), o padrão é:
1. O bloco de abertura retorna `"data": {"meu_tipo": True, ...parâmetros...}`
2. Criar bloco de fim (ex: `EndTryCatchBlock`) e adicionar em `_SKIP_TYPES`
3. No `run()`, detectar `data.get("meu_tipo")` e chamar `_find_scope_end()` + `_run_sub()`

---

### 5. `engine/execution_context.py` — Fonte da Verdade para Variáveis

**Toda a manipulação de dados em tempo de execução passa por aqui.**
O PyFlow centraliza o dicionário de variáveis e a lógica de resolução de tokens (`{{var}}`).

**Comportamento de Erro:**
Diferente de versões antigas, o PyFlow agora dispara um `ValueError` fatal se:
1. Uma variável `{{nome}}` não existir no contexto.
2. Um caminho de dot-notation `{{obj.campo}}` estiver quebrado.
O `Runner` captura esse erro, marca o passo como falha e interrompe a execução (se configurado).

**Acesso nos blocos:**
Embora `ExtractTextBlock._context` ainda exista para compatibilidade (apontando para o mesmo dict), a recomendação é usar o módulo diretamente:

```python
import engine.execution_context as ctx

# Escrita
ctx.get()["minha_var"] = "valor"

# Leitura
valor = ctx.get().get("minha_var")
```

O `ctx.clear()` é chamado automaticamente pelo Runner no início de cada fluxo (exceto em retentativas/resume).

---

### 6. `engine/api_server.py` — Servidor FastAPI local

**Modifique se precisar adicionar endpoints à API REST.**

- Usa **FastAPI + Uvicorn** (não Flask — Flask foi removido)
- Roda em thread separada via `threading.Thread`
- Porta padrão: `8080`. Se ocupada, `_find_free_port()` acha a próxima livre automaticamente
- Endpoints existentes: `GET /flows`, `POST /run`, `GET /status`, `GET /history`, `POST /stop`, `GET /dashboard`, `GET /docs`

---

### 8. 📦 Sub-Processos e Navegação Hierárquica

O PyFlow agora suporta "mergulho" em blocos. 
- O bloco `SubfluxoBlock` pode conter um parâmetro chamado `_internal_steps` (uma lista de passos serializados).
- `NodeCanvas` emite `request_enter_subflow` quando o usuário dá duplo-clique em um `SubfluxoBlock`.
- `MainWindow` gerencia uma pilha (`_parent_flows`) para permitir a navegação de volta (Breadcrumbs).

### 9. 🐜 Debugger Live Watch (Inspeção de Fios)

Os dados de execução são propagados do `Runner` para a interface.
- `ConnectionItem` (os fios) agora verifica se o nó de origem possui um `_last_result`.
- Se houver dados, o fio exibe um indicador visual (glow).
- Ao clicar no fio, a `MainWindow` abre o `DataViewer` para exibir o JSON/Texto formatado.

### 10. 🗺 Motor de Grafo (`run_graph`)

Diferente do `run()` linear, o `run_graph()` no `engine/runner.py` utiliza os IDs e as conexões (`next_success`/`next_error`) para decidir o próximo passo. Isso é essencial para sub-processos complexos que não são puramente sequenciais.

---

### 7. `engine/theme_manager.py` — Tema visual

**Modifique se precisar ajustar cores ou adicionar estilos QSS.**

- Tema único: **Catppuccin Mocha** (dark only — sem toggle)
- `colors()` → retorna o dicionário de cores
- `build_main_qss()` → retorna o QSS completo da aplicação

Paleta de cores:
```python
"bg":       "#1e1e2e"   # fundo principal
"surface":  "#181825"   # superfície (painéis)
"overlay":  "#313244"   # elementos sobre a superfície
"text":     "#cdd6f4"   # texto principal
"accent":   "#cba6f7"   # roxo destaque
"green":    "#a6e3a1"
"blue":     "#89b4fa"
"red":      "#f38ba8"
"orange":   "#fab387"
```

---

### 8. `ui/main_window.py` — Janela principal

**Modifique se precisar:**
- Adicionar botão na toolbar
- Mudar layout dos painéis
- Adicionar novo atalho de teclado

O layout usa `QSplitter` com 3 painéis: `block_panel` | `canvas` | `right_panel`.
O painel direito é composto por uma única fileira de abas unificada (`QTabWidget` com abas Props, Preview, Vars, Logs, Ajuda). A aba `Props` exibe o formulário vertical de propriedades (`PropertiesPanel`), e a aba `Preview` (`PreviewPanel` em `ui/preview_panel.py`) cuida da validação em tempo real e testes de seletores CSS.

---

## 🔄 Checklist: adicionando um bloco simples (não de controle)

```
[ ] 1. Crie o arquivo em blocks/<categoria>/nome_do_bloco.py
[ ] 2. Herde de BaseBlock, preencha name/description/category/params_schema
[ ] 3. Implemente execute() retornando {"success": bool, "message": str}
[ ] 4. Importe e adicione em ui/block_panel.py → AVAILABLE_BLOCKS
[ ] 5. Importe e adicione em ui/canvas.py → BLOCK_REGISTRY
[ ] 6. Crie um fluxo de teste em flows/teste_nome_do_bloco.json
```

---

## 🔄 Checklist: adicionando um bloco de escopo (Loop, Se, etc.)

```
[ ] 1. Crie o bloco de abertura (ex: MeuBlocoBlock) — retorna data com chave identificadora
[ ] 2. Crie o bloco de fim (ex: EndMeuBlocoBlock) — execute() retorna só success/message
[ ] 3. Adicione EndMeuBlocoBlock em runner.py → _SKIP_TYPES
[ ] 4. Em runner.py → run(), detecte data.get("meu_identificador") e use _find_scope_end()
[ ] 5. Adicione MeuBlocoBlock em canvas.py → _SCOPE_COLORS e _OPEN_TYPES
[ ] 6. Adicione EndMeuBlocoBlock em canvas.py → _CLOSE_TYPES
[ ] 7. Adicione ambos em block_panel.py → AVAILABLE_BLOCKS (abertura antes, fim depois)
[ ] 8. Adicione ambos em canvas.py → BLOCK_REGISTRY
[ ] 9. Crie fluxo de teste
```

---

## 📐 Convenções do projeto

### Nomes de arquivos
- Blocos: `snake_case.py` dentro de `blocks/<categoria>/`
- Nome da classe: `PascalCaseBlock` (sempre termina em `Block`)
- Fluxos de teste: `flows/teste_<funcionalidade>.json`

### Variáveis no fluxo
- Sintaxe de referência: `{{nome_da_variavel}}` ou `{{objeto.campo}}`
- Assets/credenciais: `{{ASSET:chave_do_asset}}`
- Erro de contexto: Se uma variável for referenciada mas não existir no dicionário de contexto, o motor dispara um `ValueError` e interrompe a execução (Fail-Fast).

### Retorno de execute()
```python
# Sucesso simples
return {"success": True, "message": "Ação concluída"}

# Sucesso com dados (para blocos de controle)
return {"success": True, "message": "...", "data": {"loop": True, "times": 3}}

# Erro
return {"success": False, "message": "Descrição do erro"}
```

### Categorias de blocos disponíveis
| Category string | Ícone | Cor |
|---|---|---|
| `"Navegador"` | 🌐 | `#89b4fa` (azul) |
| `"Controle"` | 🔧 | `#cba6f7` (roxo) |
| `"Arquivos"` | 📁 | `#a6e3a1` (verde) |
| `"Integração"` | 🔌 | `#fab387` (laranja) |
| `"Sistema"` | 💻 | `#f38ba8` (vermelho) |

---

## ⚠️ Armadilhas conhecidas — evite esses erros

### 1. Não use `blocks_count` nos blocos de controle
Os blocos Loop, Para Cada e Se **não usam mais** `blocks_count` para saber quantos blocos
são internos. O Runner detecta automaticamente os marcadores de fim (`EndLoopBlock`, etc.).
Nunca reintroduza esse parâmetro.

### 2. `_run_sub` deve sempre chamar `self.run()`
```python
def _run_sub(self, steps, base_index):
    return self.run(steps)   # ← CORRETO
```
Se `_run_sub` iterar os steps manualmente (sem chamar `run()`), aninhamentos de
Se/Loop/ForEach vão quebrar — ambos os ramos do If serão executados, por exemplo.

### 3. Modo claro foi removido
`theme_manager.py` tem apenas o tema escuro. Não existe toggle de tema.
Não tente reintroduzir `is_dark()`, `toggle()` ou `LIGHT` palette — foram deletados.

### 4. A API usa FastAPI, não Flask
`api_server.py` usa `fastapi` + `uvicorn`. Flask foi removido do projeto e do `requirements.txt`.
Não use `from flask import ...` em nenhum lugar.

### 5. Contexto de variáveis é `ExtractTextBlock._context`
É um dict estático compartilhado. Para acessar variáveis do fluxo em qualquer bloco:
```python
from blocks.browser.extract_text import ExtractTextBlock
ctx = ExtractTextBlock._context
```
Não crie outro dict de contexto em paralelo.

---

## 💬 Como pedir contexto ao usuário

Se precisar ver um arquivo que não foi fornecido, peça assim:
> "Para continuar, preciso ver o conteúdo de `ui/canvas.py`.
> Você pode colar o conteúdo ou abrir o arquivo aqui?"

Sempre confirme qual funcionalidade será adicionada antes de modificar arquivos.
Siga o padrão de criação de fluxos de teste para toda funcionalidade nova.

---

## 📋 Estado atual do projeto (referência)

| Item | Valor |
|---|---|
| Total de blocos | 51 |
| Categoria Navegador | 21 blocos |
| Categoria Controle | 15 blocos (inclui Se, Senão, FimSe, Loop, FimLoop, ParaCada, FimParaCada) |
| Categoria Arquivos | 8 blocos (inclui Ler Texto de PDF) |
| Categoria Integração | 3 blocos |
| Categoria Sistema | 5 blocos (inclui Texto para Voz TTS) |
| API | FastAPI + Uvicorn, porta 8080 (auto-detect) |
| Tema | Catppuccin Mocha (dark only) |
| Fluxos de exemplo | 30+ em `flows/` |
| Retry inteligente | ConditionalRetry por categoria: timeout, network, stale, notfound, invalid, custom |

---

*Documento gerado para handoff de desenvolvimento — PyFlow RPA*
