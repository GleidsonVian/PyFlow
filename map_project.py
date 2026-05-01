"""
map_project.py — PyFlow RPA
Mapeia toda a arquitetura do projeto e exporta para project_map.txt
Execute: python map_project.py
"""
import os
import ast
import json
from datetime import datetime

OUTPUT_FILE = "project_map.txt"

IGNORE_DIRS  = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".idea", ".vscode"}
IGNORE_FILES = {".pyc", ".pyo", ".pyd", ".git", ".DS_Store"}

CATEGORY_LABELS = {
    "blocks/browser":     "🌐 Blocos de Navegador",
    "blocks/control":     "🔧 Blocos de Controle",
    "blocks/files":       "📁 Blocos de Arquivos",
    "blocks/integration": "🔌 Blocos de Integração",
    "blocks/system":      "💻 Blocos de Sistema",
    "engine":             "⚙️  Motor de Execução",
    "ui":                 "🖥️  Interface Gráfica",
    "flows":              "💾 Fluxos Salvos",
}


# ── Utilidades de arquivo ─────────────────────────────────────────────

def count_lines(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def get_category_label(path: str) -> str:
    for prefix, label in CATEGORY_LABELS.items():
        if path.startswith(prefix):
            return label
    return ""


# ── Extração de info de arquivos ──────────────────────────────────────

def _extract_module_docstring(tree: ast.Module) -> str:
    if (tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)):
        return tree.body[0].value.s.strip().split("\n")[0]
    return ""


def _extract_class_info(node: ast.ClassDef) -> dict:
    doc = ""
    if (node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)):
        doc = node.body[0].value.s.strip().split("\n")[0]
    methods = [
        n.name for n in ast.walk(node)
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
    ]
    return {"name": node.name, "doc": doc, "methods": methods}


def get_python_info(filepath: str) -> dict:
    info = {"classes": [], "functions": [], "docstring": ""}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        info["docstring"] = _extract_module_docstring(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info["classes"].append(_extract_class_info(node))
    except Exception:
        pass
    return info


def get_json_info(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "flow_name":  data.get("flow_name", "?"),
            "steps":      len(data.get("steps", [])),
            "created_at": data.get("created_at", "")[:10],
        }
    except Exception:
        return {}


# ── Árvore de arquivos ────────────────────────────────────────────────

def build_tree(root: str) -> list:
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        depth   = rel_dir.count("/") + 1 if rel_dir else 0

        if rel_dir:
            entries.append({"type": "dir", "path": rel_dir, "depth": depth})

        for filename in sorted(filenames):
            ext = os.path.splitext(filename)[1]
            if ext in IGNORE_FILES or filename.startswith("."):
                continue
            rel_file = os.path.join(rel_dir, filename).replace("\\", "/").lstrip("/")
            entries.append({
                "type": "file",
                "path": rel_file,
                "name": filename,
                "ext":  ext,
                "abs":  os.path.join(dirpath, filename),
                "depth": depth + 1,
            })
    return entries


# ── Coleta de dados ───────────────────────────────────────────────────

def collect_blocks(entries: list) -> list:
    blocks = []
    for e in entries:
        if e["type"] == "file" and e["ext"] == ".py" and e["path"].startswith("blocks/"):
            for cls in get_python_info(e["abs"])["classes"]:
                if cls["name"].endswith("Block"):
                    blocks.append((cls["name"], e["path"], cls.get("doc", "")))
    return blocks


def collect_stats(entries: list) -> dict:
    py = json_ = lines = 0
    for e in entries:
        if e["type"] != "file":
            continue
        if e["ext"] == ".py":
            py    += 1
            lines += count_lines(e["abs"])
        elif e["ext"] == ".json":
            json_ += 1
    return {"py": py, "json": json_, "lines": lines}


# ── Formatadores de entrada ───────────────────────────────────────────

def _build_py_info_str(e: dict) -> str:
    py_info = get_python_info(e["abs"])
    classes = [c["name"] for c in py_info["classes"]]
    cls_str = f" [{', '.join(classes)}]" if classes else ""
    return f"  ({count_lines(e['abs'])} linhas{cls_str})"


def _build_json_info_str(e: dict) -> str:
    j = get_json_info(e["abs"])
    if j:
        return f"  → {j['flow_name']} | {j['steps']} passos | {j['created_at']}"
    return ""


def _build_file_info(e: dict) -> str:
    if e["ext"] == ".py":
        return _build_py_info_str(e)
    if e["ext"] == ".json" and "flows/" in e["path"]:
        return _build_json_info_str(e)
    return ""


def _format_file_entry(e: dict) -> str:
    indent = "  " * e["depth"]
    icon   = "🐍" if e["ext"] == ".py" else "📋" if e["ext"] == ".json" else "📄"
    return f"{indent}{icon} {e['name']}{_build_file_info(e)}"


def _format_dir_entry(e: dict, current_section: str) -> tuple:
    lines       = []
    indent      = "  " * e["depth"]
    cat_label   = get_category_label(e["path"])
    new_section = current_section

    if cat_label and cat_label != current_section:
        lines.append(f"\n  {cat_label}")
        new_section = cat_label

    lines.append(f"{indent}📂 {e['path'].split('/')[-1]}/")
    return lines, new_section


# ── Seções do relatório ───────────────────────────────────────────────

def _section_summary(stats: dict, block_count: int) -> list:
    return [
        "📊 SUMÁRIO",
        "-" * 40,
        f"  Arquivos Python : {stats['py']}",
        f"  Fluxos JSON     : {stats['json']}",
        f"  Linhas de código: {stats['lines']:,}",
        f"  Blocos RPA      : {block_count}",
        "",
    ]


def _section_blocks(all_blocks: list) -> list:
    lines       = ["🧩 BLOCOS DISPONÍVEIS", "-" * 40]
    current_cat = ""

    for name, path, doc in sorted(all_blocks, key=lambda x: x[1]):
        cat       = "/".join(path.split("/")[:2])
        cat_label = get_category_label(path)
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n  {cat_label or cat}")
        desc = f" — {doc}" if doc else ""
        lines.append(f"    • {name}{desc}")

    lines.append("")
    return lines


def _section_file_tree(entries: list) -> list:
    lines           = ["🗂️  ESTRUTURA DE ARQUIVOS", "-" * 40]
    current_section = ""

    for e in entries:
        if e["type"] == "dir":
            new_lines, current_section = _format_dir_entry(e, current_section)
            lines.extend(new_lines)
        else:
            lines.append(_format_file_entry(e))

    lines.append("")
    return lines


def _section_flows(root: str) -> list:
    flows_dir = os.path.join(root, "flows")
    if not os.path.exists(flows_dir):
        return []

    lines = ["💾 FLUXOS SALVOS", "-" * 40]
    for f in sorted(os.listdir(flows_dir)):
        if not f.endswith(".json"):
            continue
        j = get_json_info(os.path.join(flows_dir, f))
        if j:
            lines += [
                f"  • {j['flow_name']}",
                f"    Arquivo : {f}",
                f"    Passos  : {j['steps']}",
                f"    Criado  : {j['created_at']}",
                "",
            ]
    return lines


# ── Ponto de entrada ──────────────────────────────────────────────────

def map_project(root: str = ".") -> str:
    entries = build_tree(root)
    stats   = collect_stats(entries)
    blocks  = collect_blocks(entries)
    now     = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    sections = [
        ["=" * 70, "  PyFlow RPA — Mapa de Arquitetura do Projeto",
         f"  Gerado em: {now}", "=" * 70, ""],
        _section_summary(stats, len(blocks)),
        _section_blocks(blocks),
        _section_file_tree(entries),
        _section_flows(root),
        ["=" * 70, "  Fim do mapa de arquitetura", "=" * 70],
    ]
    return "\n".join(line for section in sections for line in section)


if __name__ == "__main__":
    print("🔍 Mapeando projeto PyFlow RPA...")
    content = map_project(".")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Mapa exportado para: {OUTPUT_FILE}")
    print()
    for line in content.split("\n")[:20]:
        print(line)
    print("...")