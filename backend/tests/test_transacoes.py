import pytest


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


def _transacao(client, **kwargs):
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


def _divida(client, valor=100, pago=20):
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


def _nova(client, **kwargs):
    base = {
        "lancamento": "Padaria",
        "tipo": "despesa",
        "categoria": "comida",
        "valor": 50.0,
        "data": "2026-05-10",
        "meio_pagamento": "pix",
        "situacao": "concluido",
        "recorrencia": "eventual",
        "observacao": None,
    }
    base.update(kwargs)
    return client.post("/api/transacoes", json=base)


def test_patch_aceita_null_em_campo_opcional(client):
    cartao = _cartao(client)
    compra = _compra(client, cartao["id"], observacao="nota")
    r = client.patch(f"/api/cartoes/compras/{compra['id']}", json={"observacao": None})
    assert r.status_code == 200
    assert r.json()["observacao"] is None


@pytest.mark.parametrize("campos", [{"tipo": "foo"}, {"valor": -10}, {"situacao": "pago"}])
def test_transacao_com_dominio_invalido_e_recusada(client, campos):
    base = {
        "lancamento": "X",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 10,
        "data": "2026-05-10",
    }
    base.update(campos)
    assert client.post("/api/transacoes", json=base).status_code == 422


def test_transacao_com_divida_inexistente_e_recusada(client):
    assert _quitacao(client, divida_id=999).status_code == 404


def test_parcela_incoerente_e_recusada(client):
    assert (
        _transacao(client, recorrencia="parcelado", parcela_atual=9, parcelas_total=8).status_code
        == 422
    )
    assert _transacao(client, recorrencia="parcelado", parcela_atual=2).status_code == 422


def test_transacao_com_descricao_so_de_espacos_ou_categoria_inexistente_e_recusada(client):
    assert _transacao(client, lancamento="   ").status_code == 422
    r = _transacao(client, categoria="naoexiste")
    assert r.status_code == 422
    assert "não está cadastrada" in r.json()["detail"]
    assert _transacao(client, meio_pagamento="xx").status_code == 422
    ok = _transacao(client, lancamento="  Luz  ").json()
    assert ok["lancamento"] == "Luz"
    assert client.patch(f"/api/transacoes/{ok['id']}", json={"categoria": "zzz"}).status_code == 422
    assert client.get(f"/api/transacoes/{ok['id']}").json()["categoria"] == "geral"


def test_validacoes_da_transacao(client):
    assert _lancamento_eventual(client, valor=0).status_code == 422
    assert _lancamento_eventual(client, data="1900-01-01").status_code == 422
    assert (
        _lancamento_eventual(
            client, parcela_atual=1, parcelas_total=3, recorrencia="mensal"
        ).status_code
        == 422
    )
    d = _divida(client)
    assert _lancamento_eventual(client, divida_id=d["id"]).status_code == 422
    r = _lancamento_eventual(client, valor=10.005)
    assert r.status_code == 201 and r.json()["valor"] in (10.0, 10.01)


def test_criar_lista_e_filtra_por_mes(client):
    _nova(client, lancamento="Maio", data="2026-05-10")
    _nova(client, lancamento="Junho", data="2026-06-10")

    r = client.get("/api/transacoes", params={"mes": 5, "ano": 2026})
    assert r.status_code == 200
    nomes = [t["lancamento"] for t in r.json()]
    assert nomes == ["Maio"]


def test_atualizar_marca_como_pago(client):
    criada = _nova(client, situacao="nao_iniciada").json()
    r = client.patch(f"/api/transacoes/{criada['id']}", json={"situacao": "concluido"})
    assert r.status_code == 200
    assert r.json()["situacao"] == "concluido"


def test_remover_transacao(client):
    criada = _nova(client).json()
    assert client.delete(f"/api/transacoes/{criada['id']}").status_code == 204
    assert client.get(f"/api/transacoes/{criada['id']}").status_code == 404


def test_filtra_por_tipo_e_categoria(client):
    _nova(client, tipo="despesa", categoria="comida")
    _nova(client, tipo="receita", categoria="salario")
    _nova(client, tipo="despesa", categoria="lazer")

    r = client.get("/api/transacoes", params={"tipo": "despesa", "categoria": "comida"})
    assert len(r.json()) == 1
    assert r.json()[0]["categoria"] == "comida"
