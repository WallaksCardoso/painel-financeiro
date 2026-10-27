def _cartao(client):
    return client.post(
        "/api/cartoes", json={"nome": "Cartão X", "dia_fechamento": 8, "dia_vencimento": 15}
    ).json()


def _compra(client, cartao_id, **kwargs):
    base = {
        "cartao_id": cartao_id,
        "descricao": "X",
        "valor_total": 100,
        "data_compra": "2026-11-01",
    }
    base.update(kwargs)
    r = client.post("/api/cartoes/compras", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def _mes(client, mes=11, ano=2026):
    r = client.get(f"/api/mes/{ano}/{mes}")
    assert r.status_code == 200, r.text
    return r.json()


def _transacao(client, **kwargs):
    base = {
        "lancamento": "X",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 100,
        "data": "2026-11-05",
        "recorrencia": "mensal",
        "situacao": "nao_iniciada",
        "meio_pagamento": "pix",
    }
    base.update(kwargs)
    r = client.post("/api/transacoes", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def test_mes_monta_gasto_fixo_como_no_notion(client):
    _transacao(
        client,
        lancamento="Salário 1",
        tipo="receita",
        categoria="salario",
        valor=3500,
        data="2026-11-05",
    )
    _transacao(
        client,
        lancamento="Salário 2",
        tipo="receita",
        categoria="salario",
        valor=1800,
        data="2026-11-20",
    )
    _transacao(client, lancamento="Aluguel", valor=200)
    _transacao(client, lancamento="Curso", valor=150, recorrencia="parcelado", data="2026-11-07")
    _transacao(client, lancamento="Conserto", valor=900, recorrencia="eventual")
    _transacao(
        client,
        lancamento="Empréstimo",
        tipo="quitacao",
        categoria="quitacao",
        valor=1000,
        recorrencia="eventual",
    )
    cartao = _cartao(client)
    _compra(client, cartao["id"], descricao="Streaming", valor_total=25.9, recorrente=True)
    _compra(
        client,
        cartao["id"],
        descricao="Geladeira",
        valor_total=1200,
        parcelas=10,
        data_compra="2026-09-07",
    )
    _compra(client, cartao["id"], descricao="Mercado", valor_total=300)

    m = _mes(client)
    assert m["fixo_conta"] == 350
    assert m["fixo_cartao"] == 145.9
    assert m["gasto_fixo"] == 495.9
    assert m["outras_despesas"] == 900
    assert m["cartao_variavel"] == 300
    assert m["total_dividas"] == 1000
    assert m["primeira_entrada"]["descricao"] == "Salário 1"
    assert m["sobra_primeira_entrada"] == round(3500 - 495.9, 2)
    assert m["livre"] == round(3500 + 1800 - 495.9 - 900 - 1000 - 300, 2)

    quantidades = {f["descricao"]: f["quantidade"] for f in m["fixos"]}
    assert quantidades == {
        "Aluguel": "Fixo",
        "Curso": "Parcelado",
        "Streaming": "Fixo",
        "Geladeira": "3/10",
    }
    assert [o["descricao"] for o in m["outras"]] == ["Conserto"]
    geladeira = next(f for f in m["fixos"] if f["descricao"] == "Geladeira")
    assert (geladeira["origem"], geladeira["dia"], geladeira["meio"]) == (
        "compra",
        15,
        "Cartão Cartão X",
    )


def test_mes_mostra_mensais_previstos_e_beneficios_a_parte(client):
    _transacao(client, lancamento="Salário", tipo="receita", valor=5000, data="2026-10-06")
    _transacao(
        client,
        lancamento="Vale-alimentação",
        tipo="beneficio",
        categoria="comida",
        valor=800,
        data="2026-10-01",
    )
    m = _mes(client)
    assert m["previstos"] == 2
    assert m["receitas"][0]["origem"] == "previsto"
    assert m["receitas"][0]["id"] is None
    assert m["total_beneficios"] == 800
    assert m["total_receitas"] == 5000
    assert m["livre"] == 5000


def test_assinatura_sem_valor_aparece_sem_valor(client):
    cartao = _cartao(client)
    _compra(client, cartao["id"], descricao="Spotify", valor_total=0, recorrente=True)
    item = _mes(client)["fixos"][0]
    assert (item["descricao"], item["valor"]) == ("Spotify", None)


def test_beneficio_nao_conta_na_projecao(client):
    _transacao(client, lancamento="Vale-alimentação", tipo="beneficio", valor=800)
    nov = client.get("/api/projecao", params={"mes": 11, "ano": 2026, "meses": 1}).json()["meses"][
        0
    ]
    assert (nov["entradas"], nov["sobra"]) == (0, 0)
    assert nov["linhas"][0]["grupo"] == "beneficio"


def test_plano_vazio_e_depois_salvo_por_mes(client):
    assert _mes(client)["plano"]["salvo"] is False
    r = client.put(
        "/api/mes/2026/11/plano",
        json={
            "meta_descricao": "Separar para dívidas",
            "meta_valor": 3000,
            "limite_cartao": 800,
            "anotacoes": "Guardar R$ 200",
        },
    )
    assert r.status_code == 200
    plano = _mes(client)["plano"]
    assert (plano["salvo"], plano["meta_valor"], plano["limite_cartao"]) == (True, 3000, 800)
    assert _mes(client, mes=12)["plano"]["salvo"] is False
    client.put("/api/mes/2026/11/plano", json={"meta_valor": 2500})
    plano = _mes(client)["plano"]
    assert (plano["meta_valor"], plano["limite_cartao"], plano["anotacoes"]) == (2500, None, None)


def test_plano_com_valor_negativo_e_recusado(client):
    assert client.put("/api/mes/2026/11/plano", json={"meta_valor": -1}).status_code == 422
