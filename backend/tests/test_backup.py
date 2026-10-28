import sqlite3
from contextlib import closing
from datetime import datetime

import pytest

from app.backup import fazer_backup, main


@pytest.fixture
def banco(tmp_path):
    caminho = tmp_path / "painel.db"
    with closing(sqlite3.connect(caminho)) as conexao:
        conexao.execute("CREATE TABLE contas (nome TEXT)")
        conexao.execute("INSERT INTO contas VALUES ('aluguel')")
        conexao.commit()
    return caminho


def test_copia_os_dados_com_a_data_no_nome(banco, tmp_path):
    destino = fazer_backup(banco, tmp_path / "copias", agora=datetime(2026, 3, 5, 8, 30, 0))

    assert destino.name == "painel-2026-03-05-083000.db"
    with closing(sqlite3.connect(destino)) as conexao:
        assert conexao.execute("SELECT nome FROM contas").fetchall() == [("aluguel",)]


def test_mantem_so_as_copias_mais_recentes(banco, tmp_path):
    pasta = tmp_path / "copias"
    for dia in range(1, 6):
        fazer_backup(banco, pasta, manter=3, agora=datetime(2026, 1, dia))

    assert [p.name for p in sorted(pasta.iterdir())] == [
        "painel-2026-01-03-000000.db",
        "painel-2026-01-04-000000.db",
        "painel-2026-01-05-000000.db",
    ]


def test_manter_zero_guarda_todas(banco, tmp_path):
    pasta = tmp_path / "copias"
    for dia in range(1, 4):
        fazer_backup(banco, pasta, manter=0, agora=datetime(2026, 1, dia))

    assert len(list(pasta.iterdir())) == 3


def test_banco_inexistente_nao_cria_arquivo(tmp_path):
    with pytest.raises(FileNotFoundError):
        fazer_backup(tmp_path / "nao-existe.db", tmp_path / "copias")

    assert not (tmp_path / "nao-existe.db").exists()


def test_sem_pasta_de_destino_falha(monkeypatch, capsys):
    monkeypatch.delenv("PAINEL_BACKUP_DIR", raising=False)

    assert main([]) == 1
    assert "PAINEL_BACKUP_DIR" in capsys.readouterr().out
