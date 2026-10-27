from datetime import date, timedelta


def _despesa(client, valor, categoria="comida", data="2026-05-10", situacao="concluido"):
    client.post(
        "/api/transacoes",
        json={
            "lancamento": "x",
            "tipo": "despesa",
            "categoria": categoria,
            "valor": valor,
            "data": data,
            "meio_pagamento": "pix",
            "situacao": situacao,
            "recorrencia": "eventual",
            "observacao": None,
        },
    )


def _receita(client, valor, data="2026-05-05"):
    client.post(
        "/api/transacoes",
        json={
            "lancamento": "salario",
            "tipo": "receita",
            "categoria": "salario",
            "valor": valor,
            "data": data,
            "meio_pagamento": "pix",
            "situacao": "concluido",
            "recorrencia": "mensal",
            "observacao": None,
        },
    )


def _setup_cartao_e_compra(client, valor=200, parcelas=1):
    cartao = client.post(
        "/api/cartoes",
        json={
            "nome": "Nubank",
            "bandeira": None,
            "limite": 5000,
            "dia_fechamento": 25,
            "dia_vencimento": 5,
            "cor": "#a78bfa",
            "ativo": True,
        },
    ).json()
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "X",
            "valor_total": valor,
            "data_compra": "2026-05-10",
            "parcelas": parcelas,
            "categoria": "geral",
            "recorrente": False,
            "tags": [],
            "observacao": None,
        },
    )
    return cartao


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


def _divida(client, valor=100, pago=20):
    return client.post(
        "/api/dividas", json={"nome": "Notebook", "valor_inicial": valor, "total_pago": pago}
    ).json()


def _transacao(client, **kwargs):
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


def test_resumo_calcula_saldo(client):
    _receita(client, 3000)
    _despesa(client, 800)
    r = client.get("/api/dashboard/resumo", params={"mes": 5, "ano": 2026}).json()
    assert r["entradas"] == 3000
    assert r["saidas"] == 800
    assert r["saldo"] == 2200


def test_resumo_conta_lancamentos_a_pagar_como_o_fluxo(client):
    _despesa(client, 500, situacao="nao_iniciada")
    r = client.get("/api/dashboard/resumo", params={"mes": 5, "ano": 2026}).json()
    fluxo = client.get("/api/projecao", params={"mes": 5, "ano": 2026, "meses": 1}).json()
    assert r["saidas"] == 500
    assert r["saldo"] == fluxo["meses"][0]["sobra"]


def test_proximas_contas_ordena_por_data(client):
    from datetime import date, timedelta

    hoje = date.today()
    d1 = (hoje + timedelta(days=2)).isoformat()
    d2 = (hoje + timedelta(days=5)).isoformat()
    _despesa(client, 100, data=d2, situacao="nao_iniciada")
    _despesa(client, 50, data=d1, situacao="nao_iniciada")

    proximas = client.get("/api/dashboard/proximas").json()
    assert len(proximas) == 2
    assert proximas[0]["valor"] == 50
    assert proximas[0]["dias_ate_vencer"] == 2


def test_dashboard_completo_inclui_fatura(client):
    cartao = client.post(
        "/api/cartoes",
        json={
            "nome": "C",
            "bandeira": None,
            "limite": 1000,
            "dia_fechamento": 25,
            "dia_vencimento": 5,
            "cor": "#a78bfa",
            "ativo": True,
        },
    ).json()
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "X",
            "valor_total": 200,
            "data_compra": "2026-05-10",
            "parcelas": 1,
            "categoria": "geral",
            "recorrente": False,
            "tags": [],
            "observacao": None,
        },
    )

    r = client.get("/api/dashboard/completo", params={"mes": 6, "ano": 2026}).json()
    assert r["fatura_aberta"] == 200.0
    assert r["resumo"]["cartao"] == 200.0
    assert r["resumo"]["saldo"] == -200.0
    assert (
        client.get("/api/dashboard/completo", params={"mes": 5, "ano": 2026}).json()[
            "fatura_aberta"
        ]
        == 0
    )


def test_dashboard_ignora_fatura_paga(client):
    cartao = _setup_cartao_e_compra(client, valor=200)
    d = client.get("/api/dashboard/completo", params={"mes": 6, "ano": 2026}).json()
    assert d["fatura_aberta"] == 200.0

    client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 5, "ano": 2026})

    d = client.get("/api/dashboard/completo", params={"mes": 6, "ano": 2026}).json()
    assert d["fatura_aberta"] == 0.0


def test_compra_no_cartao_aparece_no_grafico_por_categoria(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(
        client,
        cartao["id"],
        data_compra="2026-05-10",
        valor_total=200,
        parcelas=1,
        categoria="lazer",
    )

    categorias = client.get("/api/dashboard/por-categoria", params={"mes": 6, "ano": 2026}).json()
    lazer = next(c for c in categorias if c["categoria"] == "lazer")
    assert lazer["total"] == 200


def test_proximas_contas_incluem_quitacao_e_fatura(client):
    hoje = date.today()
    d = _divida(client, valor=5000, pago=0)
    _transacao(
        client,
        lancamento="Parcela acordo",
        tipo="quitacao",
        valor=100,
        divida_id=d["id"],
        data=(hoje + timedelta(days=3)).isoformat(),
    )
    cartao = client.post(
        "/api/cartoes",
        json={
            "nome": "Cartão X",
            "dia_fechamento": hoje.day,
            "dia_vencimento": min(hoje.day + 5, 28),
        },
    ).json()
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "Mercado",
            "valor_total": 50,
            "data_compra": hoje.isoformat(),
        },
    )
    nomes = {
        c["lancamento"] for c in client.get("/api/dashboard/completo").json()["proximas_contas"]
    }
    assert "Parcela acordo" in nomes
