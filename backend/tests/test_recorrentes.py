import threading

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.opcoes import semear


def _transacao(client, **kwargs):
    base = {
        "lancamento": "x",
        "tipo": "despesa",
        "categoria": "comida",
        "valor": 100.0,
        "data": "2026-05-10",
        "meio_pagamento": "pix",
        "situacao": "concluido",
        "recorrencia": "eventual",
        "observacao": None,
    }
    base.update(kwargs)
    return client.post("/api/transacoes", json=base).json()


def _projecao(client, mes=10, ano=2026, meses=6):
    r = client.get("/api/projecao", params={"mes": mes, "ano": ano, "meses": meses})
    assert r.status_code == 200, r.text
    return r.json()


def _lancamento_eventual_criado(client, **kwargs):
    base = {
        "lancamento": "X",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 100,
        "data": "2026-10-05",
        "recorrencia": "eventual",
    }
    base.update(kwargs)
    r = client.post("/api/transacoes", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def _lancamento_mensal(client, **kwargs):
    base = {
        "lancamento": "Conta",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 100,
        "data": "2026-10-05",
        "recorrencia": "mensal",
        "situacao": "nao_iniciada",
    }
    base.update(kwargs)
    return client.post("/api/transacoes", json=base)


def _mes(client, mes, ano=2026):
    return client.get(f"/api/mes/{ano}/{mes}").json()


def _lancamento_eventual(client, **kwargs):
    base = {
        "lancamento": "Conta",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 100,
        "data": "2026-10-05",
        "recorrencia": "eventual",
        "situacao": "nao_iniciada",
    }
    base.update(kwargs)
    return client.post("/api/transacoes", json=base)


def test_gerar_recorrentes_cria_no_mes_alvo(client):
    _transacao(
        client,
        lancamento="Aluguel",
        categoria="apartamento",
        valor=1500,
        data="2026-05-05",
        recorrencia="mensal",
    )
    criadas = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 6, "ano": 2026}
    ).json()
    assert len(criadas) == 1
    assert criadas[0]["data"] == "2026-06-05"
    assert criadas[0]["situacao"] == "nao_iniciada"


def test_gerar_recorrentes_e_idempotente(client):
    _transacao(
        client,
        lancamento="Aluguel",
        categoria="apartamento",
        valor=1500,
        data="2026-05-05",
        recorrencia="mensal",
    )
    client.post("/api/transacoes/gerar-recorrentes", params={"mes": 6, "ano": 2026})
    segunda = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 6, "ano": 2026}
    ).json()
    assert segunda == []


def test_gerar_recorrentes_ignora_eventuais(client):
    _transacao(client, lancamento="Compra única", recorrencia="eventual", data="2026-05-05")
    criadas = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 6, "ano": 2026}
    ).json()
    assert criadas == []


def test_gerar_recorrentes_ajusta_dia_curto(client):
    _transacao(
        client,
        lancamento="Assinatura",
        categoria="assinaturas",
        data="2026-01-31",
        recorrencia="mensal",
    )
    criadas = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 2, "ano": 2026}
    ).json()
    assert criadas[0]["data"] == "2026-02-27"


def test_projecao_preve_transacoes_mensais_ainda_nao_lancadas(client):
    _lancamento_eventual_criado(
        client, lancamento="Salário", tipo="receita", valor=5000, recorrencia="mensal"
    )
    _lancamento_eventual_criado(
        client, lancamento="Academia", valor=120, data="2026-10-05", recorrencia="mensal"
    )
    _lancamento_eventual_criado(
        client, lancamento="Academia", valor=90, data="2026-11-10", recorrencia="mensal"
    )

    _, nov, dez = _projecao(client, meses=3)["meses"]
    linhas_nov = {
        (linha["descricao"], linha["valor"], linha["previsto"]) for linha in nov["linhas"]
    }
    assert ("Salário", 5000, True) in linhas_nov
    assert ("Academia", 90, False) in linhas_nov
    assert ("Academia", 120, True) not in linhas_nov
    academia_dez = next(linha for linha in dez["linhas"] if linha["descricao"] == "Academia")
    assert (academia_dez["valor"], academia_dez["dia"], academia_dez["previsto"]) == (90, 10, True)
    assert dez["sobra"] == 4910


def test_mensal_no_dia_31_cai_no_ultimo_dia_de_mes_curto(client):
    _lancamento_eventual_criado(
        client, lancamento="Aluguel", valor=1000, data="2026-10-31", recorrencia="mensal"
    )
    nov = _projecao(client, meses=2)["meses"][1]
    assert nov["linhas"][0]["dia"] == 30


def test_gerar_recorrentes_em_paralelo_nao_duplica(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'concorrencia.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Sessao = sessionmaker(bind=engine, autoflush=False)
    with Sessao() as db:
        semear(db)

    def sessao_por_requisicao():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = sessao_por_requisicao
    try:
        with TestClient(app) as c:
            for i in range(5):
                _lancamento_mensal(c, lancamento=f"Conta {i}")
            resultados = []

            def gerar():
                r = c.post("/api/transacoes/gerar-recorrentes", params={"mes": 11, "ano": 2026})
                resultados.append(len(r.json()))

            threads = [threading.Thread(target=gerar) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert sum(resultados) == 5
            assert len(c.get("/api/transacoes", params={"mes": 11, "ano": 2026}).json()) == 5
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_encerrar_recorrencia_para_de_prever_e_remove_futuros_nao_pagos(client):
    _lancamento_mensal(client, lancamento="Academia", valor=120)
    client.post("/api/transacoes/gerar-recorrentes", params={"mes": 11, "ano": 2026})
    nov = client.get("/api/transacoes", params={"mes": 11, "ano": 2026}).json()[0]
    client.patch(f"/api/transacoes/{nov['id']}", json={"situacao": "concluido"})
    client.post("/api/transacoes/gerar-recorrentes", params={"mes": 12, "ano": 2026})

    r = client.post(
        "/api/transacoes/encerrar-recorrencia",
        json={"lancamento": "Academia", "categoria": "geral", "mes": 10, "ano": 2026},
    )
    assert r.json() == {"removidos": 1}
    assert client.get("/api/transacoes", params={"mes": 12, "ano": 2026}).json() == []
    assert len(client.get("/api/transacoes", params={"mes": 11, "ano": 2026}).json()) == 1
    for mes, ano in [(12, 2026), (1, 2027)]:
        assert _mes(client, mes, ano)["fixos"] == []
    assert (
        client.post("/api/transacoes/gerar-recorrentes", params={"mes": 1, "ano": 2027}).json()
        == []
    )


def test_lancar_de_novo_reinicia_a_recorrencia(client):
    _lancamento_mensal(client, lancamento="Academia")
    client.post(
        "/api/transacoes/encerrar-recorrencia",
        json={"lancamento": "Academia", "categoria": "geral", "mes": 10, "ano": 2026},
    )
    _lancamento_mensal(client, lancamento="Academia", data="2027-02-05")
    assert [f["descricao"] for f in _mes(client, 3, 2027)["fixos"]] == ["Academia"]


def test_previsto_usa_dia_habitual_e_nao_copia_observacao(client):
    for mes in (8, 9, 10):
        _lancamento_mensal(
            client,
            lancamento="Salário",
            tipo="receita",
            categoria="salario",
            data=f"2026-{mes:02d}-15",
        )
    _lancamento_mensal(
        client,
        lancamento="Salário",
        tipo="receita",
        categoria="salario",
        data="2026-11-13",
        observacao="15/11 é feriado",
    )
    receita = _mes(client, 12)["receitas"][0]
    assert (receita["origem"], receita["dia"], receita["observacao"]) == ("previsto", 15, None)
    gerada = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 12, "ano": 2026}
    ).json()[0]
    assert (gerada["data"], gerada["observacao"]) == ("2026-12-15", None)


def test_parcelado_com_numero_e_projetado_ate_a_ultima(client):
    r = _lancamento_mensal(
        client,
        lancamento="Curso",
        valor=150,
        recorrencia="parcelado",
        parcela_atual=7,
        parcelas_total=8,
        data="2026-11-07",
    )
    assert r.status_code == 201
    dez = _mes(client, 12)
    assert [(f["descricao"], f["quantidade"], f["origem"]) for f in dez["fixos"]] == [
        ("Curso", "8/8", "previsto")
    ]
    assert _mes(client, 1, 2027)["fixos"] == []
    gerada = client.post(
        "/api/transacoes/gerar-recorrentes", params={"mes": 12, "ano": 2026}
    ).json()[0]
    assert (gerada["parcela_atual"], gerada["parcelas_total"]) == (8, 8)


def test_dia_habitual_ignora_ajuste_de_feriado_e_fim_de_semana(client):
    for d in ("2026-10-15", "2026-11-13", "2027-08-13"):
        _lancamento_eventual(
            client,
            lancamento="Salário",
            tipo="receita",
            categoria="salario",
            valor=1000,
            data=d,
            recorrencia="mensal",
        )
    linhas = client.get("/api/mes/2027/9").json()["receitas"]
    assert linhas[0]["dia"] == 15


def test_previsto_em_fim_de_semana_vai_para_dia_util(client):
    _lancamento_eventual(
        client,
        lancamento="Salário",
        tipo="receita",
        categoria="salario",
        valor=1000,
        data="2027-01-06",
        recorrencia="mensal",
    )
    _lancamento_eventual(
        client, lancamento="Aluguel", valor=200, data="2027-01-06", recorrencia="mensal"
    )
    m = client.get("/api/mes/2027/2").json()
    assert m["receitas"][0]["dia"] == 5
    assert next(i for i in m["fixos"] if i["descricao"] == "Aluguel")["dia"] == 10


def test_dia_habitual_reconhece_ajuste_que_volta_dentro_do_mes(client):
    _lancamento_eventual(
        client, lancamento="Conta 31", valor=50, data="2027-01-31", recorrencia="mensal"
    )
    _lancamento_eventual(
        client, lancamento="Conta 31", valor=50, data="2027-02-26", recorrencia="mensal"
    )
    assert (
        next(
            i for i in client.get("/api/mes/2027/3").json()["fixos"] if i["descricao"] == "Conta 31"
        )["dia"]
        == 31
    )
    for d in ("2026-12-01", "2027-01-04"):
        _lancamento_eventual(
            client,
            lancamento="Ticket",
            tipo="beneficio",
            categoria="comida",
            valor=100,
            data=d,
            recorrencia="mensal",
        )
    assert client.get("/api/mes/2027/3").json()["beneficios"][0]["dia"] == 1
