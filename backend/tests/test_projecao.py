def _cartao(client, dia_fechamento=8, dia_vencimento=15):
    return client.post(
        "/api/cartoes",
        json={
            "nome": "Cartão X",
            "dia_fechamento": dia_fechamento,
            "dia_vencimento": dia_vencimento,
        },
    ).json()


def _em_andamento(client, cartao_id, **kwargs):
    base = {
        "cartao_id": cartao_id,
        "descricao": "Carro",
        "valor_parcela": 450,
        "parcela_atual": 10,
        "parcelas_total": 12,
        "mes": 10,
        "ano": 2026,
    }
    base.update(kwargs)
    return client.post("/api/cartoes/compras/em-andamento", json=base)


def _projecao(client, mes=10, ano=2026, meses=6):
    r = client.get("/api/projecao", params={"mes": mes, "ano": ano, "meses": meses})
    assert r.status_code == 200, r.text
    return r.json()


def _transacao(client, **kwargs):
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


def _cartao_simples(client, fecha=8, vence=15, nome="Cartão X"):
    r = client.post(
        "/api/cartoes", json={"nome": nome, "dia_fechamento": fecha, "dia_vencimento": vence}
    )
    return r.json()


def test_projecao_soma_entradas_contas_e_fatura_no_mes_do_vencimento(client):
    cartao = _cartao(client, dia_fechamento=25, dia_vencimento=5)
    _em_andamento(client, cartao["id"], valor_parcela=300, parcela_atual=1, parcelas_total=2)
    _transacao(client, lancamento="Salário", tipo="receita", categoria="salario", valor=5000)
    _transacao(client, lancamento="Aluguel", valor=1000)

    out, nov, dez, jan = _projecao(client, meses=4)["meses"]
    assert (out["entradas"], out["contas"], out["cartao"], out["sobra"]) == (5000, 1000, 0, 4000)
    assert nov["cartao"] == 300
    assert dez["cartao"] == 300
    assert jan["cartao"] == 0
    assert nov["acumulado"] == round(4000 + nov["sobra"], 2)


def test_projecao_mostra_quando_cada_parcela_termina(client):
    cartao = _cartao(client, dia_fechamento=8, dia_vencimento=15)
    _em_andamento(client, cartao["id"], descricao="Carro", parcela_atual=10, parcelas_total=12)
    _em_andamento(
        client,
        cartao["id"],
        descricao="Notebook",
        valor_parcela=200,
        parcela_atual=2,
        parcelas_total=10,
    )

    projecao = _projecao(client, meses=4)
    terminando = {
        (m["mes"], m["ano"]): [t["descricao"] for t in m["terminando"]] for m in projecao["meses"]
    }
    assert terminando[(12, 2026)] == ["Carro"]
    assert projecao["meses"][3]["cartao"] == 200

    ativas = {p["descricao"]: p for p in projecao["parcelas_ativas"]}
    assert (ativas["Carro"]["parcela_atual"], ativas["Carro"]["termina_mes"]) == (10, 12)
    assert (ativas["Notebook"]["termina_mes"], ativas["Notebook"]["termina_ano"]) == (6, 2027)


def test_projecao_conta_quitacoes_como_saida(client):
    _transacao(client, lancamento="Empréstimo", tipo="quitacao", categoria="quitacao", valor=500)
    out = _projecao(client, meses=1)["meses"][0]
    assert (out["quitacoes"], out["saidas"], out["sobra"]) == (500, 500, -500)


def test_parcela_futura_informa_quando_comeca(client):
    cartao = _cartao_simples(client)
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "TV",
            "valor_total": 300,
            "parcelas": 3,
            "data_compra": "2026-12-20",
        },
    )
    ativa = client.get("/api/projecao", params={"mes": 10, "ano": 2026, "meses": 1}).json()[
        "parcelas_ativas"
    ][0]
    assert (ativa["parcela_atual"], ativa["comeca_mes"], ativa["comeca_ano"]) == (0, 1, 2027)
