import re

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database import BASE_DIR, Base, inicializar_banco

ULTIMA = ScriptDirectory(str(BASE_DIR / "migrations")).get_current_head()


def _motor(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'painel.db'}")


def _diferencas(motor):
    with motor.connect() as conexao:
        return compare_metadata(MigrationContext.configure(conexao), Base.metadata)


def _versao(motor):
    with motor.connect() as conexao:
        return conexao.execute(text("SELECT version_num FROM alembic_version")).scalar()


def _criar_banco_antigo(motor):
    novas = ("divida_id", "parcela_atual", "parcelas_total", "recorrente_ate")
    with motor.begin() as conexao:
        for tabela in Base.metadata.sorted_tables:
            ddl = str(CreateTable(tabela).compile(motor))
            linhas = ddl.splitlines()
            if tabela.name == "transacoes":
                linhas = [linha for linha in linhas if not any(c in linha for c in novas)]
            if tabela.name == "orcamento_categorias":
                linhas = [linha for linha in linhas if "UNIQUE" not in linha]
            conexao.execute(text(re.sub(r",\s*\)\s*$", "\n)", "\n".join(linhas).strip())))
            for indice in tabela.indexes:
                if not any(c.name in novas for c in indice.columns):
                    conexao.execute(CreateIndex(indice))


def test_banco_novo_sai_igual_aos_modelos(tmp_path):
    motor = _motor(tmp_path)
    inicializar_banco(motor)
    assert _diferencas(motor) == []
    assert _versao(motor) == ULTIMA
    with motor.connect() as conexao:
        assert conexao.execute(text("SELECT count(*) FROM opcoes")).scalar() > 0


def test_banco_anterior_ao_alembic_e_marcado_sem_perder_dados(tmp_path):
    motor = _motor(tmp_path)
    _criar_banco_antigo(motor)
    with motor.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO transacoes (lancamento, tipo, categoria, valor, data, situacao, "
                "recorrencia, criado_em) VALUES ('Aluguel', 'despesa', 'geral', 900, "
                "'2026-10-05', 'concluido', 'mensal', '2026-10-01')"
            )
        )

    inicializar_banco(motor)

    assert _versao(motor) == ULTIMA
    assert _diferencas(motor) == []
    with motor.connect() as conexao:
        assert conexao.execute(text("SELECT lancamento FROM transacoes")).scalar() == "Aluguel"


def test_subir_duas_vezes_nao_muda_nada(tmp_path):
    motor = _motor(tmp_path)
    inicializar_banco(motor)
    inicializar_banco(motor)
    assert _diferencas(motor) == []
