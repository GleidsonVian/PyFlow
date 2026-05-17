# -*- coding: utf-8 -*-
"""Gera o GUIA_IA_PyFlow.pdf — documento de handoff para outra IA."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUTPUT = "GUIA_IA_PyFlow.pdf"

# ── Paleta Catppuccin Mocha ────────────────────────────────────────────────
BG         = colors.HexColor("#1e1e2e")
SURFACE    = colors.HexColor("#181825")
OVERLAY    = colors.HexColor("#313244")
MUTED      = colors.HexColor("#45475a")
TEXT       = colors.HexColor("#cdd6f4")
TEXT2      = colors.HexColor("#a6adc8")
ACCENT     = colors.HexColor("#cba6f7")   # roxo
GREEN      = colors.HexColor("#a6e3a1")
BLUE       = colors.HexColor("#89b4fa")
RED        = colors.HexColor("#f38ba8")
ORANGE     = colors.HexColor("#fab387")
YELLOW     = colors.HexColor("#f9e2af")
WHITE      = colors.HexColor("#cdd6f4")
BLACK_SOFT = colors.HexColor("#11111b")

# ── Estilos ────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent], **kw)
    return s

S_TITLE = style("S_TITLE", "Title",
    fontSize=26, textColor=ACCENT, spaceAfter=6,
    fontName="Helvetica-Bold", alignment=TA_CENTER)

S_SUBTITLE = style("S_SUBTITLE",
    fontSize=12, textColor=TEXT2, spaceAfter=20,
    fontName="Helvetica", alignment=TA_CENTER)

S_H1 = style("S_H1",
    fontSize=15, textColor=ACCENT, spaceBefore=18, spaceAfter=6,
    fontName="Helvetica-Bold", borderPad=4,
    backColor=OVERLAY, borderRadius=4, leftIndent=0)

S_H2 = style("S_H2",
    fontSize=12, textColor=BLUE, spaceBefore=12, spaceAfter=4,
    fontName="Helvetica-Bold")

S_BODY = style("S_BODY",
    fontSize=10, textColor=TEXT, spaceAfter=5,
    fontName="Helvetica", leading=16, alignment=TA_JUSTIFY)

S_BULLET = style("S_BULLET",
    fontSize=10, textColor=TEXT, spaceAfter=3,
    fontName="Helvetica", leftIndent=20, leading=15,
    bulletIndent=8)

S_CODE = style("S_CODE",
    fontSize=9, textColor=GREEN, spaceAfter=4, spaceBefore=4,
    fontName="Courier", backColor=BLACK_SOFT,
    leftIndent=12, rightIndent=12, leading=13,
    borderPad=6)

S_WARNING = style("S_WARNING",
    fontSize=10, textColor=RED, spaceAfter=4,
    fontName="Helvetica-Bold", leftIndent=16)

S_WARN_BODY = style("S_WARN_BODY",
    fontSize=10, textColor=TEXT, spaceAfter=3,
    fontName="Helvetica", leftIndent=28, leading=14)

S_CHECK = style("S_CHECK",
    fontSize=10, textColor=GREEN, spaceAfter=3,
    fontName="Courier", leftIndent=20, leading=14)

S_FILE_TITLE = style("S_FILE_TITLE",
    fontSize=11, textColor=ORANGE, spaceAfter=3, spaceBefore=8,
    fontName="Helvetica-Bold", leftIndent=4)

S_FOOTER = style("S_FOOTER",
    fontSize=8, textColor=MUTED, alignment=TA_CENTER)


def hr():
    return HRFlowable(width="100%", thickness=1, color=OVERLAY, spaceAfter=8, spaceBefore=4)

def h1(text):
    return Paragraph(f"  {text}", S_H1)

def h2(text):
    return Paragraph(text, S_H2)

def body(text):
    return Paragraph(text, S_BODY)

def bullet(text, symbol="•"):
    return Paragraph(f"{symbol}  {text}", S_BULLET)

def code(text):
    return Preformatted(text, S_CODE)

def warn_title(text):
    return Paragraph(f"⚠  {text}", S_WARNING)

def warn_body(text):
    return Paragraph(text, S_WARN_BODY)

def check(text):
    return Paragraph(text, S_CHECK)

def file_title(text):
    return Paragraph(text, S_FILE_TITLE)

def sp(n=6):
    return Spacer(1, n)


# ── Tabela estilizada ──────────────────────────────────────────────────────
def make_table(headers, rows, col_widths=None):
    data = [[Paragraph(f"<b>{h}</b>", style("TH",
                fontSize=10, textColor=BLACK_SOFT,
                fontName="Helvetica-Bold", alignment=TA_CENTER))
             for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), style("TD",
                fontSize=9, textColor=TEXT,
                fontName="Helvetica", leading=13))
                     for c in row])

    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, OVERLAY]),
        ("GRID",        (0, 0), (-1, -1),  0.4, MUTED),
        ("TOPPADDING",  (0, 0), (-1, -1),  5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1),  8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1),  "MIDDLE"),
    ]))
    return t


# ── Conteúdo do documento ─────────────────────────────────────────────────
def build_content():
    story = []

    # ── Capa ────────────────────────────────────────────────────────────
    story += [
        sp(40),
        Paragraph("⚡ PyFlow RPA", S_TITLE),
        Paragraph("Guia de Continuidade para IA", S_TITLE),
        sp(8),
        Paragraph(
            "Documento de orientação para uma IA assistente continuar o desenvolvimento<br/>"
            "do PyFlow RPA a partir do ponto atual.",
            S_SUBTITLE),
        sp(6),
        hr(),
        sp(4),
        Paragraph(
            "Este documento foi criado para que, ao mudar de sessão ou de IA, o desenvolvimento "
            "continue sem perda de contexto. Leia tudo antes de fazer qualquer modificação no projeto.",
            S_BODY),
        PageBreak(),
    ]

    # ── SEÇÃO 1 ──────────────────────────────────────────────────────────
    story += [
        h1("1. O que é este projeto?"),
        sp(4),
        body(
            "<b>PyFlow RPA</b> é uma ferramenta desktop de automação visual (estilo UiPath/n8n) "
            "feita em Python. O usuário arrasta blocos para um canvas, configura parâmetros e "
            "executa fluxos de automação <b>sem escrever código</b>."),
        sp(8),
    ]

    story.append(make_table(
        ["Componente", "Tecnologia / Detalhe"],
        [
            ["Interface gráfica",    "PySide6 (Qt)"],
            ["Automação web",        "Selenium + ChromeDriver"],
            ["API local",            "FastAPI + Uvicorn (porta padrão 8080, auto-detect)"],
            ["Persistência de fluxos","JSON na pasta flows/"],
            ["Tema visual",          "Catppuccin Mocha — dark only (modo claro foi REMOVIDO)"],
            ["Python",               "3.11+"],
            ["Caminho do projeto",   "C:\\Users\\Gleidson\\pasta4\\Python\\pyflow\\pyflow\\"],
        ],
        col_widths=[5*cm, 11*cm]
    ))
    story.append(sp(12))

    # ── SEÇÃO 2 ──────────────────────────────────────────────────────────
    story += [
        h1("2. Os 5 arquivos que você SEMPRE modifica ao adicionar um novo bloco"),
        sp(4),
        body("Toda vez que um novo bloco é criado, esses arquivos precisam ser tocados:"),
        sp(8),
    ]

    files = [
        (
            "FILE 1  —  blocks/<categoria>/nome_do_bloco.py  →  CRIAR",
            ORANGE,
            [
                "Crie o arquivo do bloco aqui. Todo bloco herda de BaseBlock (blocks/base_block.py).",
                "Atributos obrigatórios de classe: name (str), description (str), category (str), params_schema (list)",
                "Método obrigatório: execute(self, params: dict) -> dict",
                'Retorno mínimo: {"success": bool, "message": str}',
                'Retorno com dados (só blocos de controle): {"success": True, "message": "...", "data": {...}}',
                'Categorias válidas: "Navegador", "Controle", "Arquivos", "Integração", "Sistema"',
                "Sempre comece execute() chamando self.validate_params(params)",
            ],
            'class MeuBloco(BaseBlock):\n    name        = "Nome exibido"\n    description = "Descricao curta"\n    category    = "Controle"\n    params_schema = [\n        {"name": "param1", "label": "Rotulo", "type": "str",\n         "required": True, "default": "", "placeholder": "Exemplo"}\n    ]\n\n    def execute(self, params: dict) -> dict:\n        errors = self.validate_params(params)\n        if errors:\n            return {"success": False, "message": "\\n".join(errors)}\n        # sua logica aqui\n        return {"success": True, "message": "OK"}'
        ),
        (
            "FILE 2  —  ui/block_panel.py  →  MODIFICAR",
            BLUE,
            [
                "Painel lateral onde o usuário vê e arrasta os blocos.",
                "Passo 1: adicionar import da nova classe no topo do arquivo.",
                "Passo 2: adicionar a classe na lista AVAILABLE_BLOCKS na posição correta por categoria.",
                "A ordem em AVAILABLE_BLOCKS é exatamente a ordem exibida na interface.",
            ],
            "from blocks.minha_categoria.meu_bloco import MeuBloco\n\nAVAILABLE_BLOCKS = [\n    ...\n    MeuBloco,   # adicione na posicao correta\n    ...\n]"
        ),
        (
            "FILE 3  —  ui/canvas.py  →  MODIFICAR",
            GREEN,
            [
                "Canvas visual onde os blocos ficam após serem arrastados.",
                "Passo 1: adicionar import da nova classe no topo.",
                'Passo 2: adicionar "NomeDaClasse": NomeDaClasse no dicionário BLOCK_REGISTRY.',
                "SE o bloco for de escopo (Loop, Se, etc.): também atualizar _SCOPE_COLORS, _OPEN_TYPES ou _CLOSE_TYPES.",
            ],
            'BLOCK_REGISTRY = {\n    ...\n    "MeuBloco": MeuBloco,\n    ...\n}\n\n# Para blocos de escopo:\n_SCOPE_COLORS = {"MeuBloco": "#fab387"}  # cor da borda\n_OPEN_TYPES  = frozenset({..., "MeuBloco"})\n_CLOSE_TYPES = frozenset({..., "EndMeuBloco"})'
        ),
        (
            "FILE 4  —  engine/runner.py  →  MODIFICAR (só blocos de controle)",
            ACCENT,
            [
                "Motor de execução principal. Só mexa aqui se o bloco tiver lógica de loop, condição ou escopo.",
                "_SKIP_TYPES: frozenset com marcadores de fim que o runner ignora no loop principal.",
                "Se criar EndMeuBloco, adicione em _SKIP_TYPES.",
                "NUNCA faça _run_sub iterar steps manualmente — ele deve sempre chamar self.run(steps).",
            ],
            "_SKIP_TYPES = frozenset({\n    \"EndLoopBlock\", \"EndForEachBlock\",\n    \"EndIfBlock\", \"ElseBlock\",\n    \"EndMeuBloco\"   # adicione aqui\n})\n\ndef _run_sub(self, steps, base_index):\n    return self.run(steps)  # SEMPRE assim — nao mude"
        ),
        (
            "FILE 5  —  flows/teste_nome_do_bloco.json  →  CRIAR",
            YELLOW,
            [
                "Convenção do projeto: toda funcionalidade nova ganha um fluxo de teste JSON.",
                "Salvar em flows/ com prefixo 'teste_'.",
                "O fluxo deve exercitar o bloco em pelo menos 2-3 cenários diferentes.",
            ],
            None
        ),
    ]

    for title, color, points, code_str in files:
        col = colors.HexColor(color.hexval()) if hasattr(color, 'hexval') else color
        story.append(Paragraph(
            title,
            ParagraphStyle("FT", fontSize=11, textColor=col,
                           fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4,
                           leftIndent=4)
        ))
        for p in points:
            story.append(Paragraph(f"  →  {p}", S_BULLET))
        if code_str:
            story.append(sp(3))
            story.append(code(code_str))
        story.append(sp(4))

    story.append(PageBreak())

    # ── SEÇÃO 3 ──────────────────────────────────────────────────────────
    story += [
        h1("3. Arquitetura de Controle de Fluxo  ⚠  MUITO IMPORTANTE"),
        sp(4),
        body(
            "Os blocos <b>Loop</b>, <b>Para Cada</b> e <b>Se</b> <b>NÃO usam mais</b> o parâmetro "
            "<b>blocks_count</b> para saber quantos blocos são internos. "
            "O Runner detecta automaticamente os marcadores de fim."),
        sp(8),
        h2("Arquitetura de marcadores:"),
        bullet("Loop (Repetir)  →  abre escopo  →  usa <b>EndLoopBlock</b> para fechar"),
        bullet("Para Cada (For Each)  →  abre escopo  →  usa <b>EndForEachBlock</b> para fechar"),
        bullet("Condição (Se)  →  abre escopo  →  pode ter <b>ElseBlock</b> no meio  →  usa <b>EndIfBlock</b> para fechar"),
        bullet("Todos os marcadores de fim estão em <b>_SKIP_TYPES</b> no runner e são ignorados pelo loop principal"),
        sp(8),
        h2("Como o runner detecta o escopo:"),
        body(
            "O bloco de abertura retorna <b>data</b> com uma chave especial. "
            "O runner detecta essa chave, chama <b>_find_scope_end()</b> para achar o marcador de fim "
            "correspondente e executa os blocos internos via <b>_run_sub()</b>. "
            "O aninhamento funciona porque _run_sub chama self.run() recursivamente."),
        sp(4),
        code(
            '# Loop retorna:\n{"success": True, "data": {"loop": True, "times": 5}}\n\n'
            '# Para Cada retorna:\n{"success": True, "data": {"foreach": True, "items": [...], "variable_name": "item"}}\n\n'
            '# Se retorna:\n{"success": True, "data": {"if_result": True}}'
        ),
        sp(12),
    ]

    # ── SEÇÃO 4 ──────────────────────────────────────────────────────────
    story += [
        h1("4. Onde ficam as variáveis do fluxo"),
        sp(4),
        body(
            "O contexto de variáveis é um <b>dict estático</b> em <b>ExtractTextBlock._context</b> "
            "(arquivo: blocks/browser/extract_text.py). "
            "É compartilhado entre todos os blocos durante a execução."),
        sp(4),
        code(
            "from blocks.browser.extract_text import ExtractTextBlock\n\n"
            "# Ler uma variavel:\nvalor = ExtractTextBlock._context.get(\"minha_var\", \"\")\n\n"
            "# Escrever uma variavel:\nExtractTextBlock._context[\"minha_var\"] = \"novo_valor\""
        ),
        sp(8),
        make_table(
            ["Sintaxe nos parâmetros", "O que faz"],
            [
                ["{{nome_da_variavel}}", "Substituído pelo valor da variável antes de executar (via resolve_params())"],
                ["{{ASSET:chave}}", "Buscado no assets.json via AssetManager — para credenciais"],
            ],
            col_widths=[6*cm, 10*cm]
        ),
        sp(12),
        PageBreak(),
    ]

    # ── SEÇÃO 5 ──────────────────────────────────────────────────────────
    story += [
        h1("5. Armadilhas — erros comuns para NUNCA cometer"),
        sp(6),
    ]

    traps = [
        (
            "ARMADILHA 1: Não use blocks_count nos blocos de controle",
            "Os blocos Loop, Para Cada e Se não usam mais blocks_count. O Runner detecta os "
            "marcadores automaticamente. Nunca reintroduza esse parâmetro — vai quebrar o fluxo."
        ),
        (
            "ARMADILHA 2: _run_sub deve SEMPRE chamar self.run()",
            "Se _run_sub iterar os steps manualmente sem chamar run(), os aninhamentos de "
            "Se/Loop/ForEach vão quebrar — ambos os ramos do If serão executados. "
            "Correto: def _run_sub(self, steps, base_index): return self.run(steps)"
        ),
        (
            "ARMADILHA 3: Modo claro foi removido completamente",
            "theme_manager.py tem apenas o tema escuro Catppuccin Mocha. Não existe toggle "
            "de tema. Não reintroduza is_dark(), toggle() ou LIGHT palette — foram deletados."
        ),
        (
            "ARMADILHA 4: A API usa FastAPI, não Flask",
            "api_server.py usa fastapi + uvicorn. Flask foi removido do projeto e do "
            "requirements.txt. Não use 'from flask import ...' em nenhum lugar."
        ),
        (
            "ARMADILHA 5: Não crie outro dict de contexto",
            "Não crie uma variável global paralela para armazenar estado do fluxo. "
            "Use sempre ExtractTextBlock._context."
        ),
    ]

    for title, desc in traps:
        story.append(warn_title(title))
        story.append(warn_body(desc))
        story.append(sp(6))

    story.append(sp(8))

    # ── SEÇÃO 6 ──────────────────────────────────────────────────────────
    story += [
        h1("6. Estado atual do projeto"),
        sp(6),
        make_table(
            ["Item", "Valor"],
            [
                ["Total de blocos", "51"],
                ["Categoria Navegador", "21 blocos"],
                ["Categoria Controle", "15 blocos (Se, Senão, FimSe, Loop, FimLoop, ParaCada, FimParaCada, ...)"],
                ["Categoria Arquivos", "8 blocos (inclui Ler Texto de PDF)"],
                ["Categoria Integração", "3 blocos"],
                ["Categoria Sistema", "5 blocos (inclui Texto para Voz TTS)"],
                ["API", "FastAPI + Uvicorn — porta 8080 (auto-detect se ocupada)"],
                ["Tema", "Catppuccin Mocha (dark only)"],
                ["ConditionalRetry", "Por categoria: timeout, network, stale, notfound, invalid, custom"],
                ["Fluxos de exemplo", "30+ em flows/"],
                ["Endpoints da API", "/flows  /run  /status  /history  /stop  /dashboard  /docs"],
            ],
            col_widths=[6*cm, 10*cm]
        ),
        sp(12),
        PageBreak(),
    ]

    # ── SEÇÃO 7 ──────────────────────────────────────────────────────────
    story += [
        h1("7. Checklist — adicionando um bloco simples"),
        sp(6),
    ]
    for item in [
        "[ ]  1.  Criar blocks/<categoria>/nome_do_bloco.py herdando de BaseBlock",
        "[ ]  2.  Preencher name, description, category, params_schema",
        '[ ]  3.  Implementar execute() retornando {"success": bool, "message": str}',
        "[ ]  4.  Importar e adicionar em ui/block_panel.py  →  AVAILABLE_BLOCKS",
        "[ ]  5.  Importar e adicionar em ui/canvas.py  →  BLOCK_REGISTRY",
        "[ ]  6.  Criar flows/teste_nome_do_bloco.json",
    ]:
        story.append(check(item))
        story.append(sp(3))

    story += [
        sp(14),
        h1("8. Checklist — adicionando um bloco de escopo (Loop, Se, TryCatch...)"),
        sp(6),
    ]
    for item in [
        "[ ]  1.  Criar bloco de abertura — retorna data com chave identificadora",
        "[ ]  2.  Criar bloco de fim (EndMeuBloco) — execute() retorna só success/message",
        "[ ]  3.  Adicionar EndMeuBloco em runner.py  →  _SKIP_TYPES",
        "[ ]  4.  Em runner.py → run(), detectar data.get('meu_id') e usar _find_scope_end()",
        "[ ]  5.  Adicionar MeuBloco em canvas.py  →  _SCOPE_COLORS e _OPEN_TYPES",
        "[ ]  6.  Adicionar EndMeuBloco em canvas.py  →  _CLOSE_TYPES",
        "[ ]  7.  Adicionar ambos em block_panel.py  →  AVAILABLE_BLOCKS",
        "[ ]  8.  Adicionar ambos em canvas.py  →  BLOCK_REGISTRY",
        "[ ]  9.  Criar flows/teste_meu_bloco.json",
    ]:
        story.append(check(item))
        story.append(sp(3))

    story.append(sp(12))

    # ── SEÇÃO 9 ──────────────────────────────────────────────────────────
    story += [
        h1("9. Como se comunicar com o dono do projeto"),
        sp(6),
        bullet("Sempre confirme o que será feito <b>antes</b> de modificar arquivos"),
        bullet("Sempre peça para ver o arquivo antes de editá-lo — o usuário cola o conteúdo no chat"),
        bullet("Toda funcionalidade nova deve ganhar um fluxo de teste JSON em flows/"),
        bullet("Se precisar de um arquivo que não foi fornecido, diga exatamente qual e por quê"),
        bullet("O dono do projeto chama-se <b>Gleidson</b>"),
        bullet("O projeto é em <b>português</b> — nomes de blocos, mensagens e labels em pt-BR"),
        bullet("Prefira perguntar do que assumir — melhor confirmar um detalhe do que refazer tudo"),
        sp(20),
        hr(),
        Paragraph(
            "Documento gerado para handoff de desenvolvimento — PyFlow RPA  |  Python 3.11+  |  PySide6  |  FastAPI",
            S_FOOTER),
    ]

    return story


# ── Página com fundo escuro ────────────────────────────────────────────────
def on_page(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(BG)
    canvas_obj.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Barra superior
    canvas_obj.setFillColor(SURFACE)
    canvas_obj.rect(0, A4[1] - 18, A4[0], 18, fill=1, stroke=0)
    # Número de página
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawRightString(A4[0] - 1.5*cm, 0.6*cm, f"Página {doc.page}")
    canvas_obj.restoreState()


# ── Gerar o PDF ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.6*cm,  bottomMargin=1.8*cm,
    )
    doc.build(build_content(), onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF gerado: {OUTPUT}")
