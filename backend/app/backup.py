import argparse
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path

from .config import CAMINHO_DB

PREFIXO = "painel-"


def fazer_backup(
    origem: Path, pasta: Path, manter: int = 30, agora: datetime | None = None
) -> Path:
    if not origem.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {origem}")
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{PREFIXO}{(agora or datetime.now()):%Y-%m-%d-%H%M%S}.db"
    with closing(sqlite3.connect(origem)) as fonte, closing(sqlite3.connect(destino)) as copia:
        fonte.backup(copia)
        resultado = copia.execute("PRAGMA integrity_check").fetchone()[0]
    if resultado != "ok":
        destino.unlink()
        raise RuntimeError(f"Cópia corrompida: {resultado}")
    if manter > 0:
        for antigo in sorted(pasta.glob(f"{PREFIXO}*.db"))[:-manter]:
            antigo.unlink()
    return destino


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.backup", description="Copia o banco do painel com a data no nome."
    )
    parser.add_argument("pasta", nargs="?", default=os.environ.get("PAINEL_BACKUP_DIR"))
    parser.add_argument("--manter", type=int, default=30, help="cópias mantidas (0 = todas)")
    args = parser.parse_args(argumentos)
    if not args.pasta:
        print("Informe a pasta de destino ou defina PAINEL_BACKUP_DIR.")
        return 1
    try:
        destino = fazer_backup(Path(CAMINHO_DB), Path(args.pasta), args.manter)
    except (FileNotFoundError, RuntimeError, sqlite3.Error) as erro:
        print(f"Backup falhou: {erro}")
        return 1
    print(f"Backup salvo em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
