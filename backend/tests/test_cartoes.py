import pytest


def _criar_cartao(client, **kwargs):
    base = {
        "nome": "Nubank",
        "bandeira": "Mastercard",
        "limite": 5000.0,
        "dia_fechamento": 25,
        "dia_vencimento": 5,
        "cor": "#a78bfa",
        "ativo": True,
    }
    base.update(kwargs)
    return client.post("/api/cartoes", json=base).json()


def _criar_compra(client, cartao_id: int, **kwargs):
    base = {
        "cartao_id": cartao_id,
        "descricao": "Compra teste",
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


def _cartao(client, dia_fechamento=25, dia_vencimento=5):
    payload = {
        "nome": "Cartão Teste",
        "bandeira": None,
        "limite": 5000,
        "dia_fechamento": dia_fechamento,
        "dia_vencimento": dia_vencimento,
        "cor": "#a78bfa",
        "ativo": True,
    }
    return client.post("/api/cartoes", json=payload).json()


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


def _fatura(client, cartao_id, mes, ano):
    return client.get(f"/api/cartoes/{cartao_id}/fatura", params={"mes": mes, "ano": ano}).json()


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


def _cartao_x(client, dia_fechamento=8, dia_vencimento=15):
    return client.post(
        "/api/cartoes",
        json={
            "nome": "Cartão X",
            "dia_fechamento": dia_fechamento,
            "dia_vencimento": dia_vencimento,
        },
    ).json()


def _projecao(client, mes=10, ano=2026, meses=6):
    r = client.get("/api/projecao", params={"mes": mes, "ano": ano, "meses": meses})
    assert r.status_code == 200, r.text
    return r.json()


def _cartao_simples(client, fecha=8, vence=15, nome="Cartão X"):
    r = client.post(
        "/api/cartoes", json={"nome": nome, "dia_fechamento": fecha, "dia_vencimento": vence}
    )
    return r.json()


def test_crud_cartao(client):
    cartao = _criar_cartao(client)
    assert cartao["nome"] == "Nubank"

    r = client.patch(f"/api/cartoes/{cartao['id']}", json={"limite": 7000})
    assert r.json()["limite"] == 7000

    assert client.delete(f"/api/cartoes/{cartao['id']}").status_code == 204
    assert client.get("/api/cartoes").json() == []


def test_compra_cria_com_tags_e_recorrente(client):
    cartao = _criar_cartao(client)
    compra = _criar_compra(
        client,
        cartao["id"],
        descricao="Spotify",
        valor_total=21.90,
        recorrente=True,
        tags=["assinatura", "musica"],
    )
    assert compra["recorrente"] is True
    assert sorted(compra["tags"]) == ["assinatura", "musica"]
    assert compra["valor_parcela"] == 21.90


def test_compra_parcelada_calcula_valor_da_parcela(client):
    cartao = _criar_cartao(client)
    compra = _criar_compra(client, cartao["id"], valor_total=300.0, parcelas=3)
    assert compra["valor_parcela"] == 100.0


def test_remover_cartao_apaga_compras_em_cascata(client):
    cartao = _criar_cartao(client)
    _criar_compra(client, cartao["id"])
    _criar_compra(client, cartao["id"])

    client.delete(f"/api/cartoes/{cartao['id']}")
    assert client.get("/api/cartoes/compras").json() == []


@pytest.mark.parametrize(
    "campos",
    [{"valor_total": -50}, {"parcelas": 0}, {"descricao": None}, {"categoria": ""}],
)
def test_patch_invalido_em_compra_e_recusado_sem_gravar(client, campos):
    cartao = _cartao(client)
    compra = _compra(client, cartao["id"])
    r = client.patch(f"/api/cartoes/compras/{compra['id']}", json=campos)
    assert r.status_code == 422
    lista = client.get("/api/cartoes/compras")
    assert lista.status_code == 200
    assert lista.json()[0]["valor_total"] == 300.0


@pytest.mark.parametrize("campos", [{"dia_vencimento": 0}, {"dia_fechamento": 32}])
def test_patch_invalido_em_cartao_e_recusado(client, campos):
    cartao = _cartao(client)
    assert client.patch(f"/api/cartoes/{cartao['id']}", json=campos).status_code == 422
    assert _fatura(client, cartao["id"], 5, 2026)["total"] == 0


def test_compra_em_andamento_cai_como_parcela_atual_na_fatura_informada(client):
    cartao = _cartao_x(client)
    r = _em_andamento(client, cartao["id"])
    assert r.status_code == 201
    assert r.json()["valor_total"] == 5400
    item = _fatura(client, cartao["id"], 10, 2026)["itens"][0]
    assert (item["parcela_atual"], item["parcelas_total"], item["valor_parcela"]) == (10, 12, 450)
    assert _fatura(client, cartao["id"], 12, 2026)["itens"][0]["parcela_atual"] == 12
    assert _fatura(client, cartao["id"], 1, 2027)["itens"] == []


def test_compra_em_andamento_que_cruza_o_ano(client):
    cartao = _cartao_x(client, dia_fechamento=25, dia_vencimento=5)
    _em_andamento(client, cartao["id"], parcela_atual=3, parcelas_total=5, mes=2, ano=2027)
    assert _fatura(client, cartao["id"], 12, 2026)["itens"][0]["parcela_atual"] == 1
    assert _fatura(client, cartao["id"], 4, 2027)["itens"][0]["parcela_atual"] == 5


def test_compra_em_andamento_com_centavos_mantem_o_valor_da_parcela(client):
    cartao = _cartao_x(client)
    _em_andamento(client, cartao["id"], valor_parcela=33.33, parcela_atual=1, parcelas_total=3)
    for mes in (10, 11, 12):
        assert _fatura(client, cartao["id"], mes, 2026)["total"] == 33.33


def test_parcela_atual_maior_que_total_e_recusada(client):
    cartao = _cartao_x(client)
    assert _em_andamento(client, cartao["id"], parcela_atual=13).status_code == 422


def test_assinatura_pode_ficar_sem_valor(client):
    cartao = _cartao_x(client)
    r = client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "Netflix",
            "valor_total": 0,
            "data_compra": "2026-10-01",
            "recorrente": True,
        },
    )
    assert r.status_code == 201
    assert _projecao(client)["sem_valor"] == ["Netflix"]


def test_compra_comum_sem_valor_continua_recusada(client):
    cartao = _cartao_x(client)
    r = client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "X",
            "valor_total": 0,
            "data_compra": "2026-10-01",
        },
    )
    assert r.status_code == 422


def test_desmarcar_recorrente_de_assinatura_sem_valor_e_recusado(client):
    cartao = _cartao_x(client)
    compra = client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "Netflix",
            "valor_total": 0,
            "data_compra": "2026-10-01",
            "recorrente": True,
        },
    ).json()
    r = client.patch(f"/api/cartoes/compras/{compra['id']}", json={"recorrente": False})
    assert r.status_code == 422
    assert client.get("/api/cartoes/compras").json()[0]["recorrente"] is True


def test_assinatura_parcelada_e_recusada(client):
    cartao = _cartao_simples(client)
    r = client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "X",
            "valor_total": 30,
            "parcelas": 3,
            "recorrente": True,
            "data_compra": "2026-11-01",
        },
    )
    assert r.status_code == 422


def test_editar_compra_como_em_andamento_e_trocar_de_cartao(client):
    a = _cartao_simples(client, nome="A")
    b = _cartao_simples(client, nome="B")
    compra = client.post(
        "/api/cartoes/compras/em-andamento",
        json={
            "cartao_id": a["id"],
            "descricao": "Carro",
            "valor_parcela": 100,
            "parcela_atual": 3,
            "parcelas_total": 5,
            "mes": 11,
            "ano": 2026,
        },
    ).json()
    assert (compra["primeira_fatura_mes"], compra["primeira_fatura_ano"]) == (9, 2026)

    r = client.put(
        f"/api/cartoes/compras/{compra['id']}/em-andamento",
        json={
            "cartao_id": b["id"],
            "descricao": "Carro",
            "valor_parcela": 120,
            "parcela_atual": 4,
            "parcelas_total": 5,
            "mes": 11,
            "ano": 2026,
        },
    )
    assert r.status_code == 200
    item = client.get(f"/api/cartoes/{b['id']}/fatura", params={"mes": 11, "ano": 2026}).json()[
        "itens"
    ][0]
    assert (item["parcela_atual"], item["valor_parcela"]) == (4, 120)

    assert (
        client.patch(
            f"/api/cartoes/compras/{compra['id']}", json={"cartao_id": a["id"]}
        ).status_code
        == 200
    )
    assert (
        client.patch(f"/api/cartoes/compras/{compra['id']}", json={"cartao_id": 999}).status_code
        == 404
    )


def test_avisa_quando_parcela_cai_em_fatura_paga(client):
    cartao = _cartao_simples(client)
    client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 10, "ano": 2026})
    compra = client.post(
        "/api/cartoes/compras/em-andamento",
        json={
            "cartao_id": cartao["id"],
            "descricao": "Carro",
            "valor_parcela": 100,
            "parcela_atual": 3,
            "parcelas_total": 5,
            "mes": 11,
            "ano": 2026,
        },
    ).json()
    assert len(compra["avisos"]) == 1
    assert "2/5" in compra["avisos"][0] and "10/2026" in compra["avisos"][0]


def test_em_andamento_pelo_mes_de_vencimento(client):
    cartao = _cartao_simples(client, fecha=28, vence=5)
    client.post(
        "/api/cartoes/compras/em-andamento",
        json={
            "cartao_id": cartao["id"],
            "descricao": "TV",
            "valor_parcela": 50,
            "parcela_atual": 2,
            "parcelas_total": 4,
            "mes": 12,
            "ano": 2026,
            "vence_em": True,
        },
    )
    f = client.get(
        f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 12, "ano": 2026, "vence_em": True}
    ).json()
    assert (f["itens"][0]["parcela_atual"], f["vencimento"]) == (2, "2026-12-05")


def test_cartao_com_nome_repetido_e_recusado(client):
    client.post(
        "/api/cartoes", json={"nome": "Banco Azul", "dia_fechamento": 8, "dia_vencimento": 15}
    )
    r = client.post(
        "/api/cartoes", json={"nome": "banco azul", "dia_fechamento": 1, "dia_vencimento": 10}
    )
    assert r.status_code == 409
