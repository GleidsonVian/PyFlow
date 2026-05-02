"""
map_project.py — PyFlow RPA
Mapeia toda a arquitetura do projeto e exporta para project_map.txt
Execute: python map_project.py
"""
import os
import ast
import json
from datetime import datetime

OUTPUT_FILE  = "project_map.txt"
IGNORE_DIRS  = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".idea", ".vscode"}
IGNORE_EXTS  = {".pyc", ".pyo", ".pyd", ".git", ".DS_Store"}

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


# ── Utilidades ────────────────────────────────────────────────────────

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


# ── build_tree — CC reduzida extraindo responsabilidades atômicas ─────
# Antes CC=10: walk + filter dirs + filter files + calcular depth + montar dicts
# Agora cada função faz exatamente uma coisa

def _rel_dir(dirpath: str, root: str) -> str:
    rel = os.path.relpath(dirpath, root).replace("\\", "/")
    return "" if rel == "." else rel


def _file_entry(dirpath: str, rel_dir: str, filename: str, depth: int) -> dict | None:
    ext = os.path.splitext(filename)[1]
    if ext in IGNORE_EXTS or filename.startswith("."):
        return None
    rel = os.path.join(rel_dir, filename).replace("\\", "/").lstrip("/")
    return {"type": "file", "path": rel, "name": filename,
            "ext": ext, "abs": os.path.join(dirpath, filename), "depth": depth + 1}


def build_tree(root: str) -> list:
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        rel  = _rel_dir(dirpath, root)
        depth = rel.count("/") + 1 if rel else 0
        if rel:
            entries.append({"type": "dir", "path": rel, "depth": depth})
        entries += [e for f in sorted(filenames)
                    if (e := _file_entry(dirpath, rel, f, depth))]
    return entries


# ── get_python_info — CC reduzida separando extração de docstring e métodos ──
# Antes _extract_class_info CC=7: docstring + methods + walk misturados

def _first_docstring(node) -> str:
    """Extrai docstring do primeiro nó do body, se existir."""
    first = node.body[0] if node.body else None
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        return first.value.s.strip().split("\n")[0]
    return ""


def _public_methods(node: ast.ClassDef) -> list:
    return [n.name for n in ast.walk(node)
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]


def _extract_class_info(node: ast.ClassDef) -> dict:
    return {"name": node.name, "doc": _first_docstring(node), "methods": _public_methods(node)}


def get_python_info(filepath: str) -> dict:
    info = {"classes": [], "docstring": ""}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        info["docstring"] = _first_docstring(tree)
        info["classes"]   = [_extract_class_info(n) for n in ast.walk(tree)
                              if isinstance(n, ast.ClassDef)]
    except Exception:
        pass
    return info


def get_json_info(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"flow_name": data.get("flow_name", "?"),
                "steps":     len(data.get("steps", [])),
                "created_at": data.get("created_at", "")[:10]}
    except Exception:
        return {}


# ── Coleta ────────────────────────────────────────────────────────────

def collect_blocks(entries: list) -> list:
    blocks = []
    for e in entries:
        if e["type"] == "file" and e["ext"] == ".py" and e["path"].startswith("blocks/"):
            for cls in get_python_info(e["abs"])["classes"]:
                if cls["name"].endswith("Block"):
                    blocks.append((cls["name"], e["path"], cls.get("doc", "")))
    return blocks


def collect_stats(entries: list) -> dict:
    py = jn = lines = 0
    for e in entries:
        if e["type"] != "file":
            continue
        if e["ext"] == ".py":
            py    += 1
            lines += count_lines(e["abs"])
        elif e["ext"] == ".json":
            jn += 1
    return {"py": py, "json": jn, "lines": lines}


# ── Formatadores ──────────────────────────────────────────────────────

def _py_info_str(e: dict) -> str:
    classes = [c["name"] for c in get_python_info(e["abs"])["classes"]]
    cls_str = f" [{', '.join(classes)}]" if classes else ""
    return f"  ({count_lines(e['abs'])} linhas{cls_str})"


def _json_info_str(e: dict) -> str:
    j = get_json_info(e["abs"])
    return f"  → {j['flow_name']} | {j['steps']} passos | {j['created_at']}" if j else ""


def _file_info(e: dict) -> str:
    if e["ext"] == ".py":
        return _py_info_str(e)
    if e["ext"] == ".json" and "flows/" in e["path"]:
        return _json_info_str(e)
    return ""


def _format_file(e: dict) -> str:
    icon = "🐍" if e["ext"] == ".py" else "📋" if e["ext"] == ".json" else "📄"
    return f"{'  ' * e['depth']}{icon} {e['name']}{_file_info(e)}"


def _format_dir(e: dict, cur_section: str) -> tuple:
    lines      = []
    cat        = get_category_label(e["path"])
    new_section = cur_section
    if cat and cat != cur_section:
        lines.append(f"\n  {cat}")
        new_section = cat
    lines.append(f"{'  ' * e['depth']}📂 {e['path'].split('/')[-1]}/")
    return lines, new_section


# ── Seções ────────────────────────────────────────────────────────────

def _section_summary(stats: dict, block_count: int) -> list:
    return ["📊 SUMÁRIO", "-" * 40,
            f"  Arquivos Python : {stats['py']}",
            f"  Fluxos JSON     : {stats['json']}",
            f"  Linhas de código: {stats['lines']:,}",
            f"  Blocos RPA      : {block_count}", ""]


def _section_blocks(blocks: list) -> list:
    lines, cur = ["🧩 BLOCOS DISPONÍVEIS", "-" * 40], ""
    for name, path, doc in sorted(blocks, key=lambda x: x[1]):
        cat = "/".join(path.split("/")[:2])
        if cat != cur:
            cur = cat
            lines.append(f"\n  {get_category_label(path) or cat}")
        lines.append(f"    • {name}" + (f" — {doc}" if doc else ""))
    return lines + [""]


def _section_tree(entries: list) -> list:
    lines, section = ["🗂️  ESTRUTURA DE ARQUIVOS", "-" * 40], ""
    for e in entries:
        if e["type"] == "dir":
            new_lines, section = _format_dir(e, section)
            lines.extend(new_lines)
        else:
            lines.append(_format_file(e))
    return lines + [""]


def _section_flows(root: str) -> list:
    flows_dir = os.path.join(root, "flows")
    if not os.path.exists(flows_dir):
        return []
    lines = ["💾 FLUXOS SALVOS", "-" * 40]
    for f in sorted(os.listdir(flows_dir)):
        if f.endswith(".json"):
            j = get_json_info(os.path.join(flows_dir, f))
            if j:
                lines += [f"  • {j['flow_name']}", f"    Arquivo : {f}",
                          f"    Passos  : {j['steps']}", f"    Criado  : {j['created_at']}", ""]
    return lines


# ── Ponto de entrada ──────────────────────────────────────────────────

def map_project(root: str = ".") -> str:
    entries = build_tree(root)
    now     = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    blocks  = collect_blocks(entries)
    stats   = collect_stats(entries)

    parts = [
        ["=" * 70, "  PyFlow RPA — Mapa de Arquitetura do Projeto",
         f"  Gerado em: {now}", "=" * 70, ""],
        _section_summary(stats, len(blocks)),
        _section_blocks(blocks),
        _section_tree(entries),
        _section_flows(root),
        ["=" * 70, "  Fim do mapa de arquitetura", "=" * 70],
    ]
    return "\n".join(line for part in parts for line in part)


if __name__ == "__main__":
    print("🔍 Mapeando projeto PyFlow RPA...")
    content = map_project(".")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Mapa exportado para: {OUTPUT_FILE}")
    for line in content.split("\n")[:20]:
        print(line)
    print("...")