def _orcamento(client, **kwargs):
    base = {"mes": 5, "ano": 2026, "categoria": "comida", "teto": 500}
    base.update(kwargs)
    return client.post("/api/orcamento", json=base)


def _cartao(client, dia_fechamento=25, dia_vencimento=5):
    return client.post(
        "/api/cartoes",
        json={
            "nome": "Cartão",
            "bandeira": None,
            "limite": 5000,
            "dia_fechamento": dia_fechamento,
            "dia_vencimento": dia_vencimento,
            "cor": "#a78bfa",
            "ativo": True,
        },
    ).json()


def _compra(client, cartao_id, **kwargs):
    base = {
        "cartao_id": cartao_id,
        "descricao": "X",
        "valor_total": 300.0,
        "data_compra": "2026-05-10",
        "parcelas": 1,
        "categoria": "geral",
        "recorrente": False,
        "tags": [],
        "observacao": None,
    }
    base.update(kwargs)
    return client.post("/api/cartoes/compras", json=base).json()


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


def _despesa(client, valor, categoria="comida", data="2026-05-10"):
    client.post(
        "/api/transacoes",
        json={
            "lancamento": "x",
            "tipo": "despesa",
            "categoria": categoria,
            "valor": valor,
            "data": data,
            "meio_pagamento": "pix",
            "situacao": "concluido",
            "recorrencia": "eventual",
            "observacao": None,
        },
    )


def _orcar(client, categoria="comida", teto=500, mes=5, ano=2026):
    return client.post(
        "/api/orcamento",
        json={"mes": mes, "ano": ano, "categoria": categoria, "teto": teto},
    ).json()


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


def test_patch_invalido_em_orcamento_e_recusado(client):
    item = _orcamento(client).json()
    assert client.patch(f"/api/orcamento/{item['id']}", json={"mes": 13}).status_code == 422
    assert client.get("/api/orcamento").status_code == 200


def test_orcamento_duplicado_e_recusado(client):
    assert _orcamento(client).status_code == 201
    assert _orcamento(client, teto=900).status_code == 409


def test_patch_de_orcamento_nao_pode_criar_duplicado(client):
    _orcamento(client, categoria="comida")
    outro = _orcamento(client, categoria="lazer").json()
    r = client.patch(f"/api/orcamento/{outro['id']}", json={"categoria": "comida"})
    assert r.status_code == 409


def test_compra_no_cartao_conta_no_orcamento(client):
    cartao = _cartao(client, dia_fechamento=25)
    client.post(
        "/api/orcamento",
        json={"mes": 6, "ano": 2026, "categoria": "comida", "teto": 500},
    )
    _compra(
        client,
        cartao["id"],
        data_compra="2026-05-10",
        valor_total=200,
        parcelas=1,
        categoria="comida",
    )
    _transacao(client, categoria="comida", valor=100, data="2026-06-05")

    item = client.get("/api/orcamento", params={"mes": 6, "ano": 2026}).json()[0]
    assert item["gasto"] == 300


def test_status_ok_quando_uso_baixo(client):
    _orcar(client, teto=500)
    _despesa(client, 100)
    item = client.get("/api/orcamento", params={"mes": 5, "ano": 2026}).json()[0]
    assert item["status"] == "ok"
    assert item["uso_percentual"] == 20.0


def test_status_atencao_acima_de_80(client):
    _orcar(client, teto=100)
    _despesa(client, 90)
    item = client.get("/api/orcamento", params={"mes": 5, "ano": 2026}).json()[0]
    assert item["status"] == "atencao"


def test_status_estourou_acima_de_100(client):
    _orcar(client, teto=100)
    _despesa(client, 150)
    item = client.get("/api/orcamento", params={"mes": 5, "ano": 2026}).json()[0]
    assert item["status"] == "estourou"
    assert item["restante"] < 0


def test_so_conta_despesas_do_mes(client):
    _orcar(client, teto=500, mes=5)
    _despesa(client, 100, data="2026-05-10")
    _despesa(client, 9999, data="2026-04-10")
    item = client.get("/api/orcamento", params={"mes": 5, "ano": 2026}).json()[0]
    assert item["gasto"] == 100


def test_orcamento_com_teto_zero_e_gasto_estoura(client):
    item = client.post(
        "/api/orcamento", json={"mes": 11, "ano": 2026, "categoria": "comida", "teto": 0}
    ).json()
    _lancamento_mensal(client, categoria="comida", data="2026-11-05", recorrencia="eventual")
    item = client.get("/api/orcamento", params={"mes": 11, "ano": 2026}).json()[0]
    assert (item["status"], item["uso_percentual"]) == ("estourou", 100.0)


def test_gasto_por_categoria_e_orcamento_incluem_previstos(client):
    _lancamento_eventual(
        client, lancamento="Aluguel", categoria="apartamento", valor=507.42, recorrencia="mensal"
    )
    cats = {
        c["categoria"]: c["total"]
        for c in client.get("/api/dashboard/por-categoria?mes=1&ano=2027").json()
    }
    assert cats["apartamento"] == 507.42
    client.post(
        "/api/orcamento", json={"mes": 1, "ano": 2027, "categoria": "apartamento", "teto": 400}
    )
    item = client.get("/api/orcamento?mes=1&ano=2027").json()[0]
    assert (item["gasto"], item["status"]) == (507.42, "estourou")
