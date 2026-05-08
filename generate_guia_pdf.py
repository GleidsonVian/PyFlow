"""
Generates GUIA_IA_PyFlow.pdf — professional handoff guide for PyFlow RPA.
Uses reportlab Platypus with a dark-accent color scheme (dark blue #1e3a5f).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
DARK_BLUE   = HexColor("#1e3a5f")
MID_BLUE    = HexColor("#2d5282")
ACCENT_TEAL = HexColor("#2b7a78")
LIGHT_BG    = HexColor("#f0f4f8")
RULE_COLOR  = HexColor("#b8cce4")
WHITE       = colors.white
BLACK       = colors.black
TEXT_DARK   = HexColor("#1a1a2e")
CODE_BG     = HexColor("#eef2f7")
CODE_FG     = HexColor("#1e3a5f")
WARN_BG     = HexColor("#fff3cd")
WARN_BORDER = HexColor("#e6a817")
SUCCESS_BG  = HexColor("#d4edda")
TABLE_HEAD  = DARK_BLUE
TABLE_ALT   = HexColor("#e8f0f7")

PAGE_W, PAGE_H = A4
LEFT_MARGIN = 2.2 * cm
RIGHT_MARGIN = 2.2 * cm
TOP_MARGIN = 2.5 * cm
BOT_MARGIN = 2.2 * cm

OUTPUT_PATH = r"C:\Users\Gleidson\pasta4\Python\pyflow\pyflow\GUIA_IA_PyFlow.pdf"

# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------

class SectionHeader(Flowable):
    """Full-width dark-blue banner for section headings."""
    def __init__(self, title, width, font_size=13):
        super().__init__()
        self.title = title
        self._width = width
        self.font_size = font_size
        self.height = font_size + 14

    def draw(self):
        c = self.canv
        w, h = self._width, self.height
        # Background
        c.setFillColor(DARK_BLUE)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)
        # Text
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawString(10, h / 2 - self.font_size / 2 + 2, self.title)

    def wrap(self, availWidth, availHeight):
        return self._width, self.height


class SubHeader(Flowable):
    """Mid-blue left-accent bar for sub-headings."""
    def __init__(self, title, width, font_size=11):
        super().__init__()
        self.title = title
        self._width = width
        self.font_size = font_size
        self.height = font_size + 10

    def draw(self):
        c = self.canv
        h = self.height
        # Left accent bar
        c.setFillColor(MID_BLUE)
        c.rect(0, 2, 4, h - 4, fill=1, stroke=0)
        # Light background
        c.setFillColor(LIGHT_BG)
        c.rect(4, 0, self._width - 4, h, fill=1, stroke=0)
        # Text
        c.setFillColor(DARK_BLUE)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawString(14, h / 2 - self.font_size / 2 + 2, self.title)

    def wrap(self, availWidth, availHeight):
        return self._width, self.height


class WarnBox(Flowable):
    """Yellow warning/trap box."""
    def __init__(self, number, title, body_lines, width, styles):
        super().__init__()
        self.number = number
        self.title = title
        self.body_lines = body_lines
        self._width = width
        self.styles = styles
        self._height = None

    def _calc_height(self):
        h = 8  # top padding
        h += 14  # title row
        for _ in self.body_lines:
            h += 13
        h += 6  # bottom padding
        return h

    def draw(self):
        c = self.canv
        h = self._calc_height()
        # Border box
        c.setStrokeColor(WARN_BORDER)
        c.setFillColor(WARN_BG)
        c.roundRect(0, 0, self._width, h, 5, fill=1, stroke=1)
        # Title
        c.setFillColor(HexColor("#7d4e00"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10, h - 20, f"ARMADILHA {self.number}: {self.title}")
        # Body lines
        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica", 9)
        y = h - 34
        for line in self.body_lines:
            c.drawString(10, y, line)
            y -= 13

    def wrap(self, availWidth, availHeight):
        h = self._calc_height()
        return self._width, h


class CodeBox(Flowable):
    """Mono-spaced code-style box."""
    def __init__(self, lines, width):
        super().__init__()
        self.lines = lines
        self._width = width
        self.font_size = 8.5
        self.line_h = self.font_size + 3

    def draw(self):
        c = self.canv
        h = len(self.lines) * self.line_h + 10
        c.setFillColor(CODE_BG)
        c.setStrokeColor(RULE_COLOR)
        c.roundRect(0, 0, self._width, h, 4, fill=1, stroke=1)
        c.setFillColor(CODE_FG)
        c.setFont("Courier", self.font_size)
        y = h - self.font_size - 5
        for line in self.lines:
            c.drawString(8, y, line)
            y -= self.line_h

    def wrap(self, availWidth, availHeight):
        h = len(self.lines) * self.line_h + 10
        return self._width, h


# ---------------------------------------------------------------------------
# Page decoration (header/footer)
# ---------------------------------------------------------------------------

def make_page_decoration(doc):
    def _draw(canvas, doc):
        canvas.saveState()
        # Top rule
        canvas.setStrokeColor(DARK_BLUE)
        canvas.setLineWidth(2)
        canvas.line(LEFT_MARGIN, PAGE_H - TOP_MARGIN + 6*mm,
                    PAGE_W - RIGHT_MARGIN, PAGE_H - TOP_MARGIN + 6*mm)
        # Bottom footer
        canvas.setFillColor(DARK_BLUE)
        canvas.setFont("Helvetica", 7.5)
        footer = "PyFlow RPA  |  Guia de Continuidade para IA  |  Python 3.11+ | PySide6 | FastAPI | Maio 2026"
        canvas.drawString(LEFT_MARGIN, BOT_MARGIN - 8*mm, footer)
        # Page number right
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(PAGE_W - RIGHT_MARGIN, BOT_MARGIN - 8*mm,
                               f"Pagina {doc.page}")
        # Bottom rule
        canvas.setLineWidth(0.5)
        canvas.line(LEFT_MARGIN, BOT_MARGIN - 4*mm,
                    PAGE_W - RIGHT_MARGIN, BOT_MARGIN - 4*mm)
        canvas.restoreState()
    return _draw


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def make_styles():
    base = getSampleStyleSheet()
    content_width = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN

    styles = {}

    styles['title'] = ParagraphStyle(
        'PyTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=28,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles['subtitle'] = ParagraphStyle(
        'PySubtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=MID_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles['date'] = ParagraphStyle(
        'PyDate',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles['body'] = ParagraphStyle(
        'PyBody',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=4,
        leftIndent=2,
    )
    styles['bullet'] = ParagraphStyle(
        'PyBullet',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2,
        bulletIndent=4,
    )
    styles['code_inline'] = ParagraphStyle(
        'PyCodeInline',
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=CODE_FG,
        backColor=CODE_BG,
        spaceAfter=2,
        leftIndent=8,
    )
    styles['file_label'] = ParagraphStyle(
        'PyFileLabel',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=WHITE,
        backColor=MID_BLUE,
        spaceAfter=0,
        leftIndent=6,
    )
    styles['checklist'] = ParagraphStyle(
        'PyChecklist',
        fontName='Helvetica',
        fontSize=9.5,
        leading=15,
        textColor=TEXT_DARK,
        leftIndent=16,
        firstLineIndent=-12,
        spaceAfter=1,
    )
    styles['tip'] = ParagraphStyle(
        'PyTip',
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=HexColor("#2d6a4f"),
        leftIndent=10,
        spaceAfter=2,
    )

    return styles, content_width


# ---------------------------------------------------------------------------
# Helper: bullet item
# ---------------------------------------------------------------------------

def B(text, styles):
    return Paragraph(f"<bullet>&bull;</bullet> {text}", styles['bullet'])


def SP(n=6):
    return Spacer(1, n)


def HR(width, color=RULE_COLOR, thickness=0.5):
    return HRFlowable(width=width, thickness=thickness, color=color,
                      spaceAfter=4, spaceBefore=4)


# ---------------------------------------------------------------------------
# Build story
# ---------------------------------------------------------------------------

def build_story(styles, W):
    story = []

    # ==== COVER / TITLE BLOCK ===============================================
    story.append(SP(18))
    # Dark blue title bar
    story.append(Table(
        [[ Paragraph("Guia para IA", ParagraphStyle(
                'CoverTitle', fontName='Helvetica-Bold', fontSize=26,
                textColor=WHITE, alignment=TA_CENTER)) ],
         [ Paragraph("Continuidade do Projeto PyFlow RPA", ParagraphStyle(
                'CoverSub', fontName='Helvetica', fontSize=14,
                textColor=HexColor("#b8cce4"), alignment=TA_CENTER)) ]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
            ('TOPPADDING',    (0, 0), (-1, 0),  18),
            ('BOTTOMPADDING', (0, 0), (-1, 0),  4),
            ('TOPPADDING',    (0, 1), (-1, 1),  4),
            ('BOTTOMPADDING', (0, 1), (-1, 1),  18),
            ('ROUNDEDCORNERS', [6]),
        ])
    ))
    story.append(SP(10))
    story.append(Paragraph(
        "Documento de orientacao para uma IA assistente continuar o desenvolvimento "
        "do PyFlow RPA a partir do ponto atual.",
        styles['subtitle']
    ))
    story.append(Paragraph("Maio 2026", styles['date']))
    story.append(SP(10))
    story.append(HR(W, DARK_BLUE, 1.5))
    story.append(SP(14))

    # ==== SECTION 1 =========================================================
    story.append(SectionHeader("Secao 1 — O que e este projeto?", W))
    story.append(SP(8))
    story.append(Paragraph(
        "PyFlow RPA e uma ferramenta desktop de automacao visual (estilo UiPath/n8n) "
        "feita em Python. O usuario arrasta blocos para um canvas com nos conectados "
        "por setas bezier, configura parametros e executa fluxos de automacao sem "
        "escrever codigo.",
        styles['body']
    ))
    story.append(SP(6))

    tech_data = [
        ["Componente", "Tecnologia / Detalhe"],
        ["Interface", "PySide6 (Qt)"],
        ["Canvas", "QGraphicsView com nos draggaveis, portas Sucesso/Erro, conexoes bezier"],
        ["Automacao web", "Selenium + ChromeDriver"],
        ["API local", "FastAPI + Uvicorn (servidor embutido, porta padrao 8080)"],
        ["Fluxos salvos", "JSON na pasta flows/"],
        ["Tema", "Catppuccin Mocha (dark only — modo claro foi removido)"],
        ["Python", "3.11+"],
        ["Caminho raiz", "C:\\Users\\Gleidson\\pasta4\\Python\\pyflow\\pyflow\\"],
    ]
    story.append(_make_table(tech_data, W))
    story.append(SP(14))

    # ==== SECTION 2 =========================================================
    story.append(SectionHeader("Secao 2 — Os 5 arquivos que voce SEMPRE modifica ao adicionar um novo bloco", W))
    story.append(SP(8))

    files = [
        (
            "FILE 1 — blocks/<categoria>/nome_do_bloco.py  (CRIAR)",
            [
                "Todo bloco herda de BaseBlock (blocks/base_block.py).",
                "Atributos de classe obrigatorios: name, description, category, params_schema",
                "Metodo execute(self, params: dict) -> dict",
                'Retorno padrao: {"success": bool, "message": str}',
                'Retorno com dados: {"success": True, "message": "...", "data": {...}}',
                'Categorias validas: "Navegador", "Controle", "Arquivos", "Integracao", "Sistema"',
                "Sempre inicie execute() chamando self.validate_params(params)",
            ]
        ),
        (
            "FILE 2 — ui/block_panel.py  (MODIFICAR)",
            [
                "Adicionar import da nova classe.",
                "Adicionar a classe na lista AVAILABLE_BLOCKS na posicao correta por categoria.",
            ]
        ),
        (
            "FILE 3 — ui/node_canvas.py  (MODIFICAR)",
            [
                'Adicionar import + "NomeDaClasse": NomeDaClasse no dicionario BLOCK_REGISTRY.',
                "Se for bloco de escopo: tambem atualizar _SCOPE_COLORS, _OPEN_TYPES, _CLOSE_TYPES.",
            ]
        ),
        (
            "FILE 4 — engine/runner.py  (MODIFICAR — so para blocos de controle de fluxo)",
            [
                "Se o bloco tiver logica de loop/condicao.",
                "_SKIP_TYPES = frozenset com marcadores de fim.",
                "NUNCA faca _run_sub iterar steps manualmente — deve sempre chamar self.run(steps).",
            ]
        ),
        (
            'FILE 5 — flows/teste_nome_do_bloco.json  (CRIAR)',
            [
                'Toda funcionalidade nova ganha um fluxo de teste JSON em flows/ com prefixo "teste_".',
            ]
        ),
    ]

    for file_title, lines in files:
        story.append(KeepTogether([
            _file_label(file_title, W, styles),
            SP(3),
            *[B(l, styles) for l in lines],
            SP(6),
        ]))

    story.append(SP(6))

    # ==== SECTION 3 =========================================================
    story.append(SectionHeader("Secao 3 — Arquitetura do Canvas de Nos (MUITO IMPORTANTE)", W))
    story.append(SP(8))
    story.append(Paragraph(
        "O canvas foi COMPLETAMENTE REESCRITO para o modelo de nos estilo n8n. "
        "Arquivo principal: <font name='Courier' size='9'>ui/node_canvas.py</font>",
        styles['body']
    ))
    story.append(SP(6))

    classes_data = [
        ["Classe", "Descricao"],
        ["PortItem", "Porta de conexao. port_type in (\"input\", \"success\", \"error\").\n"
                     "Cores: input=#8b8fa8 | success=#a6e3a1 | error=#f38ba8"],
        ["ConnectionItem", "Seta bezier entre portas. Colorida conforme porta de origem."],
        ["NodeItem", "No visual. Tres portas: in_port (esq), success_port (dir-sup), error_port (dir-inf).\n"
                     "Suporta pin de output e estado running/success/error."],
        ["NodeScene", "Gerencia nos e conexoes. Metodo get_graph() retorna grafo para o runner."],
        ["_NodeView", "QGraphicsView com RubberBandDrag (selecao multipla), pan por botao do meio, zoom por scroll."],
        ["NodeCanvas", "Widget publico. API identica ao Canvas original para compatibilidade."],
    ]
    story.append(_make_table(classes_data, W))
    story.append(SP(8))

    story.append(SubHeader("Interacao do usuario no canvas", W))
    story.append(SP(4))
    interactions = [
        "Arrastar no espaco vazio: selecao multipla (rubber band roxo)",
        "Arrastar com botao do meio do mouse: pan",
        "Scroll: zoom in/out",
        "Del: apaga nos/conexoes selecionados",
        "Ctrl+D: duplica nos selecionados",
        "Ctrl+Z / Ctrl+Y: desfaz / refaz",
        "Duplo clique no no: edita parametros",
        "Clique direito no no: menu contextual (editar, executar, fixar output, duplicar, remover)",
        "Snap to grid: nos se alinham ao grid de 24px automaticamente",
    ]
    for i in interactions:
        story.append(B(i, styles))
    story.append(SP(14))

    # ==== SECTION 4 =========================================================
    story.append(SectionHeader("Secao 4 — Execucao Condicional por Saida (Sucesso/Erro)", W))
    story.append(SP(8))

    ports_data = [
        ["Porta", "Cor", "Ativada quando..."],
        ["success_port", "Verde (#a6e3a1)", 'execute() retorna {"success": True, ...}'],
        ["error_port",   "Vermelha (#f38ba8)", 'execute() retorna {"success": False, ...}'],
    ]
    story.append(_make_table(ports_data, W))
    story.append(SP(6))

    story.append(SubHeader("Runner — run_graph() em engine/runner.py", W))
    story.append(SP(4))
    runner_steps = [
        "Detecta raizes (nos sem entradas)",
        "Executa cada no, le o resultado success/fail",
        "Segue a aresta correta (next_success ou next_error)",
        "Set visited previne loops infinitos",
    ]
    for s in runner_steps:
        story.append(B(s, styles))
    story.append(SP(6))

    story.append(SubHeader("Serializacao JSON dos nos", W))
    story.append(SP(4))
    serial_lines = [
        "_next_success  — ID do no de destino em caso de sucesso",
        "_next_error    — ID do no de destino em caso de erro",
        "_next (legado) — tratado como _next_success (retrocompatibilidade)",
        "Arquivo de teste: flows/demo_condicional.json",
    ]
    story.append(CodeBox(serial_lines, W))
    story.append(SP(14))

    # ==== SECTION 5 =========================================================
    story.append(SectionHeader("Secao 5 — Arquitetura de Controle de Fluxo", W))
    story.append(SP(8))
    story.append(Paragraph(
        "Os blocos Loop, Para Cada e Se usam o modelo de marcadores de escopo. "
        "O Runner detecta marcadores automaticamente — nao sao usados blocks_count.",
        styles['body']
    ))
    story.append(SP(6))

    scope_data = [
        ["Bloco de abertura", "Marcador de fim"],
        ["Loop (Repetir)",         "EndLoopBlock"],
        ["Para Cada (For Each)",   "EndForEachBlock"],
        ["Condicao (Se)",          "ElseBlock (opcional) -> EndIfBlock"],
    ]
    story.append(_make_table(scope_data, W))
    story.append(SP(6))

    story.append(Paragraph(
        "Todos os marcadores de fim estao em <font name='Courier' size='9'>_SKIP_TYPES</font> no runner.",
        styles['body']
    ))
    story.append(SP(4))
    story.append(SubHeader("Chaves especiais retornadas pelo bloco de abertura", W))
    story.append(SP(4))
    key_lines = [
        '{"loop": True, "times": 3}',
        '{"foreach": True, "items": [...]}',
        '{"if_result": True/False}',
    ]
    story.append(CodeBox(key_lines, W))
    story.append(SP(6))
    story.append(Paragraph(
        "O runner detecta a chave, chama _find_scope_end() para achar o marcador e "
        "executa os blocos internos via _run_sub(). Aninhamento funciona porque "
        "_run_sub chama self.run() recursivamente.",
        styles['body']
    ))
    story.append(SP(14))

    # ==== SECTION 6 =========================================================
    story.append(SectionHeader("Secao 6 — Onde ficam as variaveis do fluxo", W))
    story.append(SP(8))

    var_data = [
        ["Operacao", "Codigo"],
        ["Ler variavel",    "ExtractTextBlock._context.get(\"minha_var\", \"\")"],
        ["Escrever variavel", "ExtractTextBlock._context[\"minha_var\"] = \"valor\""],
        ["Contexto (arquivo)", "blocks/browser/extract_text.py — dict estatico _context"],
        ["Sintaxe nos params", "{{nome_da_variavel}} — substituido por resolve_params() no runner"],
        ["Assets/credenciais", "{{ASSET:chave}} — buscado no assets.json via AssetManager"],
    ]
    story.append(_make_table(var_data, W))
    story.append(SP(14))

    # ==== SECTION 7 =========================================================
    story.append(SectionHeader("Secao 7 — Estado atual do projeto", W))
    story.append(SP(8))

    status_data = [
        ["Item", "Valor"],
        ["Total de blocos",        "49"],
        ["Categoria Navegador",    "21 blocos"],
        ["Categoria Controle",     "15 blocos (Loop, ForEach, Se, Else, FimLoop, FimForEach, FimSe...)"],
        ["Categoria Arquivos",     "7 blocos"],
        ["Categoria Integracao",   "3 blocos"],
        ["Categoria Sistema",      "4 blocos"],
        ["API",                    "FastAPI + Uvicorn, porta 8080 (auto-detect se ocupada)"],
        ["Tema",                   "Catppuccin Mocha (dark only)"],
        ["Canvas",                 "Node-based com portas Sucesso/Erro, bezier, snap to grid"],
        ["Selecao multipla",       "RubberBandDrag + mover grupo"],
        ["Atalhos",                "Del, Ctrl+D, Ctrl+Z, Ctrl+Y"],
        ["Icone do app",           "assets/icon.png + assets/icon.ico (gerado por assets/generate_icon.py)"],
        ["Fluxos de exemplo",      "30+ em flows/"],
    ]
    story.append(_make_table(status_data, W))
    story.append(SP(14))

    # ==== SECTION 8 =========================================================
    story.append(PageBreak())
    story.append(SectionHeader("Secao 8 — Armadilhas — erros comuns para NUNCA cometer", W))
    story.append(SP(8))

    traps = [
        (1, "Nao use blocks_count nos blocos de controle",
         ["Loop, Para Cada e Se nao usam mais blocks_count.",
          "O Runner detecta os marcadores automaticamente."]),
        (2, "_run_sub deve sempre chamar self.run()",
         ["Se _run_sub iterar os steps manualmente, aninhamentos vao quebrar.",
          "Sempre delegar a recursao para self.run(steps)."]),
        (3, "Modo claro foi removido completamente",
         ["theme_manager.py tem apenas o tema escuro Catppuccin Mocha.",
          "Nao existe toggle de tema."]),
        (4, "A API usa FastAPI, nao Flask",
         ["api_server.py usa fastapi + uvicorn.",
          "Flask foi removido do projeto."]),
        (5, "Nao crie outro dict de contexto",
         ["Nao crie variavel global paralela para estado do fluxo.",
          "Use sempre ExtractTextBlock._context."]),
        (6, "Pan no canvas usa botao do MEIO",
         ["O botao esquerdo no espaco vazio faz selecao multipla (rubber band).",
          "Pan = botao do meio do mouse."]),
        (7, "Canvas e node_canvas.py, nao canvas.py",
         ["O arquivo foi renomeado/substituido.",
          "O import em main_window.py e: from ui.node_canvas import NodeCanvas as Canvas"]),
    ]

    for num, title, lines in traps:
        story.append(WarnBox(num, title, lines, W, styles))
        story.append(SP(6))

    story.append(SP(8))

    # ==== SECTION 9 =========================================================
    story.append(SectionHeader("Secao 9 — Checklist rapido — adicionando um bloco simples", W))
    story.append(SP(8))

    simple_steps = [
        ("1", "Criar", "blocks/<categoria>/nome_do_bloco.py herdando de BaseBlock"),
        ("2", "Preencher", "name, description, category, params_schema na classe"),
        ("3", "Implementar", 'execute() retornando {"success": bool, "message": str}'),
        ("4", "Registrar", "Importar e adicionar em ui/block_panel.py -> AVAILABLE_BLOCKS"),
        ("5", "Registrar", "Importar e adicionar em ui/node_canvas.py -> BLOCK_REGISTRY"),
        ("6", "Testar", "Criar flows/teste_nome_do_bloco.json"),
    ]
    checklist_data = [["#", "Acao", "Detalhe"]] + [[n, a, d] for n, a, d in simple_steps]
    story.append(_make_table(checklist_data, W, col_widths=[0.06, 0.18, 0.76]))
    story.append(SP(14))

    # ==== SECTION 10 =========================================================
    story.append(SectionHeader("Secao 10 — Checklist — adicionando um bloco de escopo (Loop, Se, etc.)", W))
    story.append(SP(8))

    scope_steps = [
        ("1", "Bloco de abertura", "Retorna data com chave identificadora especial"),
        ("2", "Bloco de fim",      "EndMeuBloco — execute() retorna so success/message"),
        ("3", "runner.py",         "Adicionar EndMeuBloco em _SKIP_TYPES"),
        ("4", "runner.py",         "Detectar data.get(\"meu_identificador\") e usar _find_scope_end()"),
        ("5", "node_canvas.py",    "Adicionar MeuBloco em _SCOPE_COLORS e _OPEN_TYPES"),
        ("6", "node_canvas.py",    "Adicionar EndMeuBloco em _CLOSE_TYPES"),
        ("7", "block_panel.py",    "Adicionar ambos em AVAILABLE_BLOCKS"),
        ("8", "node_canvas.py",    "Adicionar ambos em BLOCK_REGISTRY"),
        ("9", "Teste",             "Criar flows/teste_meu_bloco.json"),
    ]
    scope_data2 = [["#", "Arquivo / Etapa", "O que fazer"]] + [[n, a, d] for n, a, d in scope_steps]
    story.append(_make_table(scope_data2, W, col_widths=[0.06, 0.24, 0.70]))
    story.append(SP(14))

    # ==== SECTION 11 =========================================================
    story.append(SectionHeader("Secao 11 — Dicas de comunicacao com o usuario", W))
    story.append(SP(8))

    tips = [
        "Confirmar o que sera feito antes de modificar arquivos.",
        "Pedir para ver o arquivo antes de editar.",
        "Toda funcionalidade nova deve ganhar fluxo de teste JSON em flows/.",
        "Se precisar de arquivo nao fornecido, dizer exatamente qual e por que.",
        "O dono do projeto chama-se Gleidson.",
        "O projeto e em portugues (nomes de blocos, mensagens, labels — tudo em pt-BR).",
        "O usuario prefere confirmacao antes de mudancas grandes.",
    ]
    for t in tips:
        story.append(B(t, styles))

    story.append(SP(16))

    # ==== FOOTER BOX =========================================================
    story.append(HR(W, DARK_BLUE, 1.5))
    story.append(SP(6))
    story.append(Table(
        [[Paragraph(
            "Documento gerado para handoff de desenvolvimento — "
            "PyFlow RPA | Python 3.11+ | PySide6 | FastAPI | Maio 2026",
            ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=8.5,
                           textColor=WHITE, alignment=TA_CENTER)
        )]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [4]),
        ])
    ))

    return story


# ---------------------------------------------------------------------------
# Table helper
# ---------------------------------------------------------------------------

def _make_table(data, total_width, col_widths=None):
    """Build a styled two-column (or n-column) table."""
    n_cols = len(data[0])

    if col_widths is None:
        if n_cols == 2:
            cw = [total_width * 0.30, total_width * 0.70]
        elif n_cols == 3:
            cw = [total_width * 0.08, total_width * 0.30, total_width * 0.62]
        else:
            cw = [total_width / n_cols] * n_cols
    else:
        cw = [total_width * f for f in col_widths]

    # Wrap all cells in Paragraphs
    cell_style = ParagraphStyle(
        'TC', fontName='Helvetica', fontSize=8.5, leading=12, textColor=TEXT_DARK
    )
    header_style = ParagraphStyle(
        'TH', fontName='Helvetica-Bold', fontSize=8.5, leading=12, textColor=WHITE
    )

    table_data = []
    for r_idx, row in enumerate(data):
        table_row = []
        for cell in row:
            style = header_style if r_idx == 0 else cell_style
            table_row.append(Paragraph(str(cell), style))
        table_data.append(table_row)

    # Alternating row colors
    ts = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEAD),
        ('GRID', (0, 0), (-1, -1), 0.4, RULE_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT]),
    ]

    t = Table(table_data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(ts))
    return t


def _file_label(text, width, styles):
    return Table(
        [[Paragraph(text, ParagraphStyle(
            'FL', fontName='Courier-Bold', fontSize=9,
            textColor=WHITE, leading=12
        ))]],
        colWidths=[width],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), MID_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [3]),
        ])
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
        title="Guia para IA — Continuidade do Projeto PyFlow RPA",
        author="PyFlow RPA — Gleidson Viana",
        subject="Handoff document for AI assistant",
        creator="reportlab / generate_guia_pdf.py",
    )

    page_deco = make_page_decoration(doc)
    styles, W = make_styles()
    story = build_story(styles, W)

    doc.build(story, onFirstPage=page_deco, onLaterPages=page_deco)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
