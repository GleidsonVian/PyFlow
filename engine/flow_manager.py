import json
import os
from datetime import datetime


class FlowManager:
    """
    Responsável por salvar e carregar fluxos em formato JSON.
    """

    FLOWS_DIR = "flows"

    def __init__(self, flows_dir: str = None):
        self.flows_dir = flows_dir or self.FLOWS_DIR
        os.makedirs(self.flows_dir, exist_ok=True)

    def save(self, flow_name: str, steps: list[dict]) -> str:
        """
        Salva um fluxo em arquivo JSON.

        Args:
            flow_name: nome do fluxo (vira nome do arquivo)
            steps: lista de passos no formato serializado:
                   [{"block": "open_browser", "params": {...}}]

        Returns:
            Caminho do arquivo salvo.
        """
        safe_name = flow_name.strip().replace(" ", "_").lower()
        filepath = os.path.join(self.flows_dir, f"{safe_name}.json")

        payload = {
            "flow_name": flow_name,
            "created_at": datetime.now().isoformat(),
            "steps": steps
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"Fluxo salvo em: {filepath}")
        return filepath

    def load(self, filepath: str) -> dict:
        """
        Carrega um fluxo a partir de um arquivo JSON.

        Returns:
            Dict com "flow_name" e "steps".
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def list_flows(self) -> list[str]:
        """Retorna lista de caminhos de todos os fluxos salvos."""
        if not os.path.exists(self.flows_dir):
            return []
        return [
            os.path.join(self.flows_dir, f)
            for f in os.listdir(self.flows_dir)
            if f.endswith(".json")
        ]

    def delete(self, filepath: str) -> bool:
        """Remove um arquivo de fluxo."""
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False