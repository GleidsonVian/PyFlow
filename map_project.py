"""
map_project.py — PyFlow RPA
Mapeia toda a arquitetura do projeto e exporta para project_map.txt
Execute: python map_project.py
"""
import os
import ast
import importlib.util
from datetime import datetime

OUTPUT_FILE = "project_map.txt"

# Pastas e arquivos a ignorar
IGNORE_DIRS  = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".idea", ".vscode"}
IGNORE_FILES = {".pyc", ".pyo", ".pyd", ".git", ".DS_Store"}

# Categorias conhecidas do projeto
CATEGORY_LABELS = {
    "blocks/browser":     "🌐 Blocos de Navegador",
    "blocks/control":     "🔧 Blocos de Controle",
    "blocks/files":       "📁 Blocos de Arquivos",
    "blocks/integration": "🔌 Blocos de Integração",
    "engine":             "⚙️  Motor de Execução",
    "ui":                 "🖥️  Interface Gráfica",
    "flows":              "💾 Fluxos Salvos",
}


def get_python_info(filepath: str) -> dict:
    """Extrai classes, funções e docstring de um arquivo Python."""
    info = {"classes": [], "functions": [], "docstring": ""}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        # Docstring do módulo
        if (isinstance(tree.body[0], ast.Expr) and
                isinstance(tree.body[0].value, ast.Constant)):
            info["docstring"] = tree.body[0].value.s.strip().split("\n")[0]

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Pega docstring da classe
                class_doc = ""
                if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant)):
                    class_doc = node.body[0].value.s.strip().split("\n")[0]

                # Métodos públicos
                methods = [
                    n.name for n in ast.walk(node)
                    if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
                ]
                info["classes"].append({
                    "name": node.name,
                    "doc": class_doc,
                    "methods": methods
                })

            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                # Apenas funções de nível de módulo (não dentro de classes)
                if any(isinstance(p, ast.Module) for p in ast.walk(tree)
                       if hasattr(p, 'body') and node in getattr(p, 'body', [])):
                    info["functions"].append(node.name)

    except Exception:
        pass
    return info


def get_json_info(filepath: str) -> dict:
    """Extrai info básica de um arquivo JSON de fluxo."""
    import json
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "flow_name": data.get("flow_name", "?"),
            "steps": len(data.get("steps", [])),
            "created_at": data.get("created_at", "")[:10]
        }
    except Exception:
        return {}


def build_tree(root: str) -> list:
    """Constrói a árvore de arquivos do projeto."""
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filtra pastas ignoradas
        dirnames[:] = sorted([d for d in dirnames if d not in IGNORE_DIRS])

        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir == ".":
            rel_dir = ""

        depth = rel_dir.count("/") + 1 if rel_dir else 0

        if rel_dir:
            entries.append({"type": "dir", "path": rel_dir, "depth": depth})

        for filename in sorted(filenames):
            ext = os.path.splitext(filename)[1]
            if ext in IGNORE_FILES or filename.startswith("."):
                continue
            filepath = os.path.join(dirpath, filename)
            rel_file = os.path.join(rel_dir, filename).replace("\\", "/").lstrip("/")
            entries.append({
                "type": "file",
                "path": rel_file,
                "name": filename,
                "ext": ext,
                "abs": filepath,
                "depth": depth + 1
            })

    return entries


def get_category_label(path: str) -> str:
    for prefix, label in CATEGORY_LABELS.items():
        if path.startswith(prefix):
            return label
    return ""


def count_lines(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def format_size(filepath: str) -> str:
    try:
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size}B"
        return f"{size // 1024}KB"
    except Exception:
        return "?"


def map_project(root: str = ".") -> str:
    lines = []
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    lines.append("=" * 70)
    lines.append("  PyFlow RPA — Mapa de Arquitetura do Projeto")
    lines.append(f"  Gerado em: {now}")
    lines.append("=" * 70)
    lines.append("")

    # ── Sumário ──────────────────────────────────────────────────────────
    total_py = total_json = total_lines = 0
    all_blocks = []

    entries = build_tree(root)
    for e in entries:
        if e["type"] == "file":
            if e["ext"] == ".py":
                total_py += 1
                total_lines += count_lines(e["abs"])
                if e["path"].startswith("blocks/"):
                    info = get_python_info(e["abs"])
                    for cls in info["classes"]:
                        if cls["name"].endswith("Block"):
                            all_blocks.append((cls["name"], e["path"], cls.get("doc", "")))
            elif e["ext"] == ".json":
                total_json += 1

    lines.append("📊 SUMÁRIO")
    lines.append("-" * 40)
    lines.append(f"  Arquivos Python : {total_py}")
    lines.append(f"  Fluxos JSON     : {total_json}")
    lines.append(f"  Linhas de código: {total_lines:,}")
    lines.append(f"  Blocos RPA      : {len(all_blocks)}")
    lines.append("")

    # ── Blocos disponíveis ────────────────────────────────────────────────
    lines.append("🧩 BLOCOS DISPONÍVEIS")
    lines.append("-" * 40)
    current_cat = ""
    for name, path, doc in sorted(all_blocks, key=lambda x: x[1]):
        cat = "/".join(path.split("/")[:2])
        cat_label = get_category_label(path)
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n  {cat_label or cat}")
        desc = f" — {doc}" if doc else ""
        lines.append(f"    • {name}{desc}")
    lines.append("")

    # ── Árvore de arquivos ────────────────────────────────────────────────
    lines.append("🗂️  ESTRUTURA DE ARQUIVOS")
    lines.append("-" * 40)

    current_section = ""
    for e in entries:
        indent = "  " * e["depth"]

        if e["type"] == "dir":
            cat_label = get_category_label(e["path"])
            section = cat_label or ""
            if section and section != current_section:
                current_section = section
                lines.append(f"\n  {section}")
            lines.append(f"{indent}📂 {e['path'].split('/')[-1]}/")

        elif e["type"] == "file":
            ext = e["ext"]
            icon = "🐍" if ext == ".py" else "📋" if ext == ".json" else "📄"
            info_str = ""

            if ext == ".py":
                n_lines = count_lines(e["abs"])
                py_info = get_python_info(e["abs"])
                classes = [c["name"] for c in py_info["classes"]]
                class_str = f" [{', '.join(classes)}]" if classes else ""
                info_str = f"  ({n_lines} linhas{class_str})"

            elif ext == ".json" and "flows/" in e["path"]:
                j = get_json_info(e["abs"])
                if j:
                    info_str = f"  → {j.get('flow_name','?')} | {j.get('steps','?')} passos | {j.get('created_at','')}"

            lines.append(f"{indent}{icon} {e['name']}{info_str}")

    lines.append("")

    # ── Fluxos salvos ─────────────────────────────────────────────────────
    flows_dir = os.path.join(root, "flows")
    if os.path.exists(flows_dir):
        lines.append("💾 FLUXOS SALVOS")
        lines.append("-" * 40)
        for f in sorted(os.listdir(flows_dir)):
            if f.endswith(".json"):
                j = get_json_info(os.path.join(flows_dir, f))
                if j:
                    lines.append(f"  • {j['flow_name']}")
                    lines.append(f"    Arquivo : {f}")
                    lines.append(f"    Passos  : {j['steps']}")
                    lines.append(f"    Criado  : {j['created_at']}")
                    lines.append("")

    lines.append("=" * 70)
    lines.append("  Fim do mapa de arquitetura")
    lines.append("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    print("🔍 Mapeando projeto PyFlow RPA...")
    content = map_project(".")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Mapa exportado para: {OUTPUT_FILE}")
    print()
    # Preview do sumário
    for line in content.split("\n")[:20]:
        print(line)
    print("...")
