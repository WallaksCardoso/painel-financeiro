from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends
from sqlalchemy import Connection, create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import BASE_DIR, DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def _ativar_chaves_estrangeiras(conexao_dbapi, _registro) -> None:
    if conexao_dbapi.__class__.__module__.startswith("sqlite3"):
        cursor = conexao_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Db = Annotated[Session, Depends(get_db)]


def _config_alembic(conexao: Connection) -> Config:
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
    cfg.attributes["connection"] = conexao
    return cfg


def inicializar_banco(motor: Engine = engine) -> None:
    from . import models  # noqa: F401

    with motor.begin() as conexao:
        tabelas = set(inspect(conexao).get_table_names())
        cfg = _config_alembic(conexao)
        if tabelas and "alembic_version" not in tabelas:
            Base.metadata.create_all(bind=conexao)
            _completar_banco_legado(conexao, tabelas)
            command.stamp(cfg, REVISAO_INICIAL)
        command.upgrade(cfg, "head")

    from .services.opcoes import semear

    with Session(motor) as db:
        semear(db)


REVISAO_INICIAL = "0001"


def _completar_banco_legado(conexao: Connection, tabelas: set[str]) -> None:
    if "transacoes" in tabelas:
        colunas = {c["name"] for c in inspect(conexao).get_columns("transacoes")}
        for coluna, tipo in [
            ("divida_id", "INTEGER"),
            ("parcela_atual", "INTEGER"),
            ("parcelas_total", "INTEGER"),
            ("recorrente_ate", "DATE"),
        ]:
            if coluna not in colunas:
                conexao.execute(text(f"ALTER TABLE transacoes ADD COLUMN {coluna} {tipo}"))
        for coluna in ("data", "tipo", "categoria", "divida_id"):
            conexao.execute(
                text(f"CREATE INDEX IF NOT EXISTS ix_transacoes_{coluna} ON transacoes ({coluna})")
            )
    if "compras_cartao" in tabelas:
        for coluna in ("data_compra", "cartao_id"):
            conexao.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_compras_cartao_{coluna} "
                    f"ON compras_cartao ({coluna})"
                )
            )
    if "orcamento_categorias" in tabelas:
        conexao.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_orcamento_mes_categoria "
                "ON orcamento_categorias (mes, ano, categoria)"
            )
        )
    if {"transacoes", "dividas"} <= tabelas:
        conexao.execute(
            text(
                "UPDATE transacoes SET divida_id = NULL WHERE divida_id IS NOT NULL "
                "AND divida_id NOT IN (SELECT id FROM dividas)"
            )
        )
    if {"faturas_pagas", "cartoes"} <= tabelas:
        conexao.execute(
            text("DELETE FROM faturas_pagas WHERE cartao_id NOT IN (SELECT id FROM cartoes)")
        )
