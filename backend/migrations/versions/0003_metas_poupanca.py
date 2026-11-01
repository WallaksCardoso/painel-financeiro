import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "metas_poupanca" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "metas_poupanca",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("orcamento_variavel", sa.Float(), nullable=True),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mes", "ano", name="uq_meta_poupanca_inicio"),
    )


def downgrade() -> None:
    op.drop_table("metas_poupanca")
