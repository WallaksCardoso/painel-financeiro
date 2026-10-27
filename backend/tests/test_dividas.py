def _divida(client, **kwargs):
    base = {"nome": "Carro", "valor_inicial": 100.0, "total_pago": 0.0}
    base.update(kwargs)
    return client.post("/api/dividas", json=base).json()


def _quitacao(client, divida_id, valor=100.0):
    return client.post(
        "/api/transacoes",
        json={
            "lancamento": "Parcela",
            "tipo": "quitacao",
            "categoria": "quitacao",
            "valor": valor,
            "data": "2026-05-10",
            "situacao": "concluido",
            "divida_id": divida_id,
        },
    )


def _criar(client, **kwargs):
    base = {
        "nome": "Carro",
        "valor_inicial": 1000.0,
        "total_pago": 0.0,
        "prazo": "2026-12-31",
        "status": "em_andamento",
        "prioridade": "alta",
        "observacao": None,
    }
    base.update(kwargs)
    return client.post("/api/dividas", json=base).json()


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


def _divida_com_pago(client, valor=100, pago=20):
    return client.post(
        "/api/dividas", json={"nome": "Notebook", "valor_inicial": valor, "total_pago": pago}
    ).json()


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


def test_divida_nova_nao_herda_quitacao_de_divida_apagada(client):
    antiga = _divida(client)
    _quitacao(client, antiga["id"], valor=50)
    client.delete(f"/api/dividas/{antiga['id']}")
    nova = _divida(client)
    assert nova["pago_vinculado"] == 0
    assert client.get("/api/transacoes").json()[0]["divida_id"] is None


def test_divida_volta_a_em_andamento_ao_apagar_a_quitacao(client):
    d = _divida(client)
    t = _quitacao(client, d["id"]).json()
    assert client.get("/api/dividas").json()[0]["status"] == "concluido"
    client.delete(f"/api/transacoes/{t['id']}")
    d = client.get("/api/dividas").json()[0]
    assert d["status"] == "em_andamento"
    assert d["restante"] == 100


def test_divida_reabre_ao_aumentar_valor_inicial(client):
    d = _divida(client)
    _quitacao(client, d["id"])
    r = client.patch(f"/api/dividas/{d['id']}", json={"valor_inicial": 200})
    assert r.json()["status"] == "em_andamento"


def test_trocar_quitacao_de_divida_recalcula_as_duas(client):
    a = _divida(client, nome="A")
    b = _divida(client, nome="B")
    t = _quitacao(client, a["id"]).json()
    client.patch(f"/api/transacoes/{t['id']}", json={"divida_id": b["id"]})
    status = {d["nome"]: d["status"] for d in client.get("/api/dividas").json()}
    assert status == {"A": "em_andamento", "B": "concluido"}


def test_status_definido_a_mao_prevalece(client):
    d = _divida(client)
    r = client.patch(f"/api/dividas/{d['id']}", json={"status": "concluido"})
    assert r.json()["status"] == "concluido"


def test_dividas_ordenadas_por_prioridade(client):
    for p in ["baixa", "alta", "media"]:
        _divida(client, nome=p, prioridade=p)
    assert [d["nome"] for d in client.get("/api/dividas").json()] == ["alta", "media", "baixa"]


def test_progresso_calculado_no_create(client):
    d = _criar(client, valor_inicial=1000, total_pago=250)
    assert d["restante"] == 750
    assert d["progresso"] == 25.0


def test_pagar_total_marca_como_concluida(client):
    d = _criar(client, valor_inicial=1000, total_pago=0)
    r = client.patch(f"/api/dividas/{d['id']}", json={"total_pago": 1000})
    assert r.json()["status"] == "concluido"
    assert r.json()["progresso"] == 100.0
    assert r.json()["restante"] == 0.0


def test_pagar_acima_do_inicial_e_recusado(client):
    d = _criar(client, valor_inicial=500, total_pago=0)
    r = client.patch(f"/api/dividas/{d['id']}", json={"total_pago": 600})
    assert r.status_code == 422
    assert client.get("/api/dividas").json()[0]["total_pago"] == 0


def test_divida_criada_ja_quitada_nasce_concluida(client):
    d = _criar(client, valor_inicial=500, total_pago=500)
    assert d["status"] == "concluido"


def test_divida_com_valor_zero_e_recusada(client):
    r = client.post("/api/dividas", json={"nome": "X", "valor_inicial": 0})
    assert r.status_code == 422


def test_quitacao_vinculada_abate_divida(client):
    divida = client.post(
        "/api/dividas",
        json={
            "nome": "Carro",
            "valor_inicial": 1000,
            "total_pago": 0,
            "prazo": None,
            "status": "em_andamento",
            "prioridade": "alta",
            "observacao": None,
        },
    ).json()
    _transacao(
        client,
        tipo="quitacao",
        categoria="quitacao",
        valor=400,
        situacao="concluido",
        divida_id=divida["id"],
    )
    atualizada = client.get("/api/dividas").json()[0]
    assert atualizada["pago_vinculado"] == 400
    assert atualizada["pago_efetivo"] == 400
    assert atualizada["restante"] == 600
    assert atualizada["progresso"] == 40.0


def test_quitacao_vinculada_conclui_a_divida(client):
    divida = client.post(
        "/api/dividas",
        json={
            "nome": "Carro",
            "valor_inicial": 500,
            "total_pago": 0,
            "prazo": None,
            "status": "em_andamento",
            "prioridade": "alta",
            "observacao": None,
        },
    ).json()
    _transacao(
        client,
        tipo="quitacao",
        categoria="quitacao",
        valor=500,
        situacao="concluido",
        divida_id=divida["id"],
    )
    assert client.get("/api/dividas").json()[0]["status"] == "concluido"


def test_quitacao_pendente_nao_abate(client):
    divida = client.post(
        "/api/dividas",
        json={
            "nome": "Carro",
            "valor_inicial": 1000,
            "total_pago": 0,
            "prazo": None,
            "status": "em_andamento",
            "prioridade": "alta",
            "observacao": None,
        },
    ).json()
    _transacao(
        client,
        tipo="quitacao",
        categoria="quitacao",
        valor=400,
        situacao="nao_iniciada",
        divida_id=divida["id"],
    )
    assert client.get("/api/dividas").json()[0]["pago_vinculado"] == 0


def test_quitacao_nao_passa_do_que_falta_da_divida(client):
    d = _divida_com_pago(client)
    r = _lancamento_eventual(
        client, tipo="quitacao", valor=200, divida_id=d["id"], situacao="concluido"
    )
    assert r.status_code == 422
    assert "R$ 80,00" in r.json()["detail"]
    ok = _lancamento_eventual(
        client, tipo="quitacao", valor=80, divida_id=d["id"], situacao="concluido"
    )
    assert ok.status_code == 201
    assert client.patch(f"/api/transacoes/{ok.json()['id']}", json={"valor": 80}).status_code == 200
    assert client.patch(f"/api/transacoes/{ok.json()['id']}", json={"valor": 81}).status_code == 422


def test_ajuste_manual_da_divida_considera_quitacoes(client):
    d = _divida_com_pago(client, valor=3000, pago=0)
    _lancamento_eventual(
        client, tipo="quitacao", valor=500, divida_id=d["id"], situacao="concluido"
    )
    r = client.patch(f"/api/dividas/{d['id']}", json={"total_pago": 2800})
    assert r.status_code == 422
    assert client.patch(f"/api/dividas/{d['id']}", json={"total_pago": 2500}).status_code == 200
