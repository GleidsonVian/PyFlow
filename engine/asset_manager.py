import json
import os

class AssetManager:
    ASSETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets.json")

    @classmethod
    def list_assets(cls) -> dict:
        """Retorna todos os assets cadastrados."""
        if not os.path.exists(cls.ASSETS_FILE):
            return {}
        try:
            with open(cls.ASSETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    @classmethod
    def get_asset(cls, key):
        return cls.list_assets().get(key)
    
    @classmethod
    def save_assets(cls, assets_dict: dict):
        """Sobrescreve o arquivo com o novo dicionário."""
        with open(cls.ASSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(assets_dict, f, indent=4, ensure_ascii=False)

    @classmethod
    def set_asset(cls, key, value):
        assets = {}
        if os.path.exists(cls.ASSETS_FILE):
            with open(cls.ASSETS_FILE, 'r') as f:
                assets = json.load(f)
        assets[key] = value
        with open(cls.ASSETS_FILE, 'w') as f:
            json.dump(assets, f, indent=4)