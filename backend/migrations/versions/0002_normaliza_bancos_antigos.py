import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspetor = sa.inspect(op.get_bind())

    chaves = inspetor.get_foreign_keys("transacoes")
    if not any(fk["constrained_columns"] == ["divida_id"] for fk in chaves):
        with op.batch_alter_table("transacoes", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_transacoes_divida_id", "dividas", ["divida_id"], ["id"], ondelete="SET NULL"
            )

    restricoes = {u["name"] for u in inspetor.get_unique_constraints("orcamento_categorias")}
    if "uq_orcamento_mes_categoria" not in restricoes:
        op.drop_index("uq_orcamento_mes_categoria", table_name="orcamento_categorias")
        with op.batch_alter_table("orcamento_categorias", recreate="always") as batch_op:
            batch_op.create_unique_constraint(
                "uq_orcamento_mes_categoria", ["mes", "ano", "categoria"]
            )


def downgrade() -> None:
    pass
