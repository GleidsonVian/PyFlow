import json
import os
from datetime import datetime
from pathlib import Path

_BASE_DIR = Path(__file__).parent.parent


class FlowManager:
    """
    Responsável por salvar e carregar fluxos em formato JSON.
    """

    FLOWS_DIR = str(_BASE_DIR / "flows")
    AUTOSAVE_FILE = str(_BASE_DIR / "flows" / ".autosave.json")

    def __init__(self, flows_dir: str = None):
        self.flows_dir = flows_dir or self.FLOWS_DIR
        os.makedirs(self.flows_dir, exist_ok=True)

    def save(self, flow_name: str, steps: list[dict], filepath: str = None) -> str:
        """
        Salva um fluxo em arquivo JSON.
        Se filepath for fornecido, salva diretamente nele (sem gerar nome).
        """
        if filepath:
            safe_path = filepath
            flow_name = flow_name or Path(filepath).stem
        else:
            safe_name = flow_name.strip().replace(" ", "_").lower()
            safe_path = os.path.join(self.flows_dir, f"{safe_name}.json")

        payload = {
            "flow_name": flow_name,
            "saved_at": datetime.now().isoformat(),
            "steps": steps,
        }

        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return safe_path

    def autosave(self, steps: list[dict]):
        """Salva silenciosamente em .autosave.json a cada mudança no canvas."""
        if not steps:
            return
        payload = {
            "flow_name": "__autosave__",
            "saved_at": datetime.now().isoformat(),
            "steps": steps,
        }
        with open(self.AUTOSAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def has_autosave(self) -> bool:
        return os.path.exists(self.AUTOSAVE_FILE)

    def load_autosave(self) -> dict:
        return self.load(self.AUTOSAVE_FILE)

    def clear_autosave(self):
        if os.path.exists(self.AUTOSAVE_FILE):
            os.remove(self.AUTOSAVE_FILE)

    def load(self, filepath: str) -> dict:
        """Carrega um fluxo a partir de um arquivo JSON."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_flows(self) -> list[str]:
        """Retorna lista de caminhos de todos os fluxos salvos (exclui autosave)."""
        if not os.path.exists(self.flows_dir):
            return []
        return [
            os.path.join(self.flows_dir, f)
            for f in os.listdir(self.flows_dir)
            if f.endswith(".json") and not f.startswith(".")
        ]

    def delete(self, filepath: str) -> bool:
        """Remove um arquivo de fluxo."""
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
