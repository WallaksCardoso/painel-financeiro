from alembic import context
from sqlalchemy import Connection

from app import models  # noqa: F401
from app.config import DATABASE_URL
from app.database import Base, engine

alvo = Base.metadata


def _rodar(conexao: Connection) -> None:
    context.configure(connection=conexao, target_metadata=alvo, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=DATABASE_URL, target_metadata=alvo, literal_binds=True, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    conexao = context.config.attributes.get("connection")
    if conexao is not None:
        _rodar(conexao)
    else:
        with engine.connect() as nova:
            _rodar(nova)
            nova.commit()
