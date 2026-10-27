import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cartoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("bandeira", sa.String(length=40), nullable=True),
        sa.Column("limite", sa.Float(), nullable=False),
        sa.Column("dia_fechamento", sa.Integer(), nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("cor", sa.String(length=20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "configuracoes",
        sa.Column("chave", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("chave"),
    )
    op.create_table(
        "dividas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("valor_inicial", sa.Float(), nullable=False),
        sa.Column("total_pago", sa.Float(), nullable=False),
        sa.Column("prazo", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("prioridade", sa.String(length=20), nullable=False),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "movimentos_reserva",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("origem", sa.String(length=50), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "opcoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grupo", sa.String(length=30), nullable=False),
        sa.Column("chave", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grupo", "chave", name="uq_opcao_grupo_chave"),
    )
    with op.batch_alter_table("opcoes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_opcoes_grupo"), ["grupo"], unique=False)

    op.create_table(
        "orcamento_categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.Column("teto", sa.Float(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mes", "ano", "categoria", name="uq_orcamento_mes_categoria"),
    )
    op.create_table(
        "planos_mes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("meta_descricao", sa.String(length=200), nullable=True),
        sa.Column("meta_valor", sa.Float(), nullable=True),
        sa.Column("limite_cartao", sa.Float(), nullable=True),
        sa.Column("anotacoes", sa.String(length=4000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mes", "ano", name="uq_plano_mes"),
    )
    op.create_table(
        "compras_cartao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cartao_id", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=200), nullable=False),
        sa.Column("valor_total", sa.Float(), nullable=False),
        sa.Column("data_compra", sa.Date(), nullable=False),
        sa.Column("parcelas", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.Column("recorrente", sa.Boolean(), nullable=False),
        sa.Column("tags_csv", sa.String(length=300), nullable=False),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cartao_id"], ["cartoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("compras_cartao", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_compras_cartao_cartao_id"), ["cartao_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_compras_cartao_data_compra"), ["data_compra"], unique=False
        )

    op.create_table(
        "faturas_pagas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cartao_id", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("pago_em", sa.Date(), nullable=False),
        sa.Column("valor_pago", sa.Float(), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cartao_id"], ["cartoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cartao_id", "mes", "ano", name="uq_fatura_cartao_mes"),
    )
    op.create_table(
        "transacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lancamento", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("meio_pagamento", sa.String(length=30), nullable=True),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("recorrencia", sa.String(length=20), nullable=False),
        sa.Column("divida_id", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("parcela_atual", sa.Integer(), nullable=True),
        sa.Column("parcelas_total", sa.Integer(), nullable=True),
        sa.Column("recorrente_ate", sa.Date(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["divida_id"], ["dividas.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("transacoes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_transacoes_categoria"), ["categoria"], unique=False)
        batch_op.create_index(batch_op.f("ix_transacoes_data"), ["data"], unique=False)
        batch_op.create_index(batch_op.f("ix_transacoes_divida_id"), ["divida_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_transacoes_tipo"), ["tipo"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("transacoes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_transacoes_tipo"))
        batch_op.drop_index(batch_op.f("ix_transacoes_divida_id"))
        batch_op.drop_index(batch_op.f("ix_transacoes_data"))
        batch_op.drop_index(batch_op.f("ix_transacoes_categoria"))

    op.drop_table("transacoes")
    op.drop_table("faturas_pagas")
    with op.batch_alter_table("compras_cartao", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_compras_cartao_data_compra"))
        batch_op.drop_index(batch_op.f("ix_compras_cartao_cartao_id"))

    op.drop_table("compras_cartao")
    op.drop_table("planos_mes")
    op.drop_table("orcamento_categorias")
    with op.batch_alter_table("opcoes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_opcoes_grupo"))

    op.drop_table("opcoes")
    op.drop_table("movimentos_reserva")
    op.drop_table("dividas")
    op.drop_table("configuracoes")
    op.drop_table("cartoes")
