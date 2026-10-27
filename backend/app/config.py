import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CAMINHO_DB = os.environ.get("PAINEL_DB", str(BASE_DIR / "painel.db"))
DATABASE_URL = f"sqlite:///{CAMINHO_DB}"

ORIGENS_CORS = ["http://localhost:5173", "http://127.0.0.1:5173"]
