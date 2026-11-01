from datetime import date

from app.services.metas import semanas_restantes


def _meta(client, **kwargs):
    base = {"valor": 1000, "orcamento_variavel": 500, "mes": 1, "ano": 2090}
    base.update(kwargs)
    r = client.post("/api/metas", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def _transacao(client, **kwargs):
    base = {
        "lancamento": "X",
        "tipo": "despesa",
        "categoria": "geral",
        "valor": 100,
        "data": "2090-01-05",
        "recorrencia": "eventual",
        "situacao": "concluido",
        "meio_pagamento": "pix",
    }
    base.update(kwargs)
    r = client.post("/api/transacoes", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def _aporte(client, valor, data="2090-01-06", tipo="aporte"):
    r = client.post(
        "/api/reserva", json={"descricao": "Caixinha", "tipo": tipo, "valor": valor, "data": data}
    )
    assert r.status_code == 201, r.text


def _mes(client, mes=1, ano=2090):
    r = client.get(f"/api/mes/{ano}/{mes}")
    assert r.status_code == 200, r.text
    return r.json()


def _projecao(client, mes=1, ano=2090, meses=3):
    r = client.get("/api/projecao", params={"mes": mes, "ano": ano, "meses": meses})
    assert r.status_code == 200, r.text
    return r.json()["meses"]


def test_crud_de_meta(client):
    meta = _meta(client)
    assert client.get("/api/metas").json() == [meta]

    r = client.put(f"/api/metas/{meta['id']}", json={**meta, "valor": 1500})
    assert r.status_code == 200
    assert r.json()["valor"] == 1500

    assert client.delete(f"/api/metas/{meta['id']}").status_code == 204
    assert client.get("/api/metas").json() == []


def test_duas_metas_comecando_no_mesmo_mes_sao_recusadas(client):
    _meta(client)
    r = client.post("/api/metas", json={"valor": 200, "mes": 1, "ano": 2090})
    assert r.status_code == 409


def test_meta_vale_a_partir_do_mes_de_inicio_e_a_mais_recente_vence(client):
    _meta(client, valor=1000, mes=1, ano=2090)
    _meta(client, valor=1500, mes=3, ano=2090)

    assert _mes(client, 12, 2089)["meta"]["valor"] is None
    assert _mes(client, 1, 2090)["meta"]["valor"] == 1000
    assert _mes(client, 2, 2090)["meta"]["valor"] == 1000
    assert _mes(client, 3, 2090)["meta"]["valor"] == 1500
    assert _mes(client, 3, 2090)["meta"]["origem"] == "recorrente"


def test_meta_do_plano_do_mes_substitui_a_recorrente(client):
    _meta(client, valor=1000)
    client.put("/api/mes/2090/2/plano", json={"meta_valor": 400})

    fevereiro = _mes(client, 2, 2090)["meta"]
    assert fevereiro["valor"] == 400
    assert fevereiro["origem"] == "mes"
    assert _mes(client, 3, 2090)["meta"]["valor"] == 1000


def test_guardado_soma_reserva_liquida_e_investimentos(client):
    _meta(client, valor=1000)
    _aporte(client, 700)
    _aporte(client, 100, tipo="saque", data="2090-01-20")
    _transacao(client, tipo="investimento", categoria="reserva", valor=150)

    meta = _mes(client)["meta"]
    assert meta["guardado"] == 750
    assert meta["falta"] == 250


def test_sem_meta_nao_falta_nada_mesmo_com_saque(client):
    _aporte(client, 500, data="2089-12-10")
    _aporte(client, 200, tipo="saque", data="2090-01-20")

    meta = _mes(client)["meta"]
    assert meta["valor"] is None
    assert meta["guardado"] == -200
    assert meta["falta"] == 0


def test_livre_para_gastar_desconta_fixos_dividas_meta_e_variavel(client):
    _meta(client, valor=1000)
    _transacao(client, lancamento="Salário", tipo="receita", categoria="salario", valor=5000)
    _transacao(client, lancamento="Aluguel", valor=1200, recorrencia="mensal")
    _transacao(client, lancamento="Dívida", tipo="quitacao", categoria="quitacao", valor=300)
    _transacao(client, lancamento="Mercado", valor=400)

    livre = _mes(client)["livre_para_gastar"]
    assert livre["disponivel"] == 2500
    assert livre["gasto_variavel"] == 400
    assert livre["restante"] == 2100
    assert livre["semanas"] == 5
    assert livre["por_semana"] == 420


def test_guardar_mais_que_a_meta_reduz_o_livre(client):
    _meta(client, valor=1000)
    _transacao(client, lancamento="Salário", tipo="receita", categoria="salario", valor=5000)
    _aporte(client, 1800)

    livre = _mes(client)["livre_para_gastar"]
    assert livre["disponivel"] == 3200


def test_projecao_desconta_meta_e_variavel_estimado(client):
    _meta(client, valor=1000, orcamento_variavel=500)
    _transacao(
        client,
        lancamento="Salário",
        tipo="receita",
        categoria="salario",
        valor=3000,
        recorrencia="mensal",
    )

    janeiro, fevereiro, _ = _projecao(client)
    assert janeiro["sobra"] == 3000
    assert janeiro["meta"] == 1000
    assert janeiro["variavel_estimado"] == 500
    assert janeiro["depois_da_meta"] == 1500
    assert fevereiro["depois_da_meta"] == 1500


def test_projecao_sem_meta_nao_calcula_depois_da_meta(client):
    mes = _projecao(client, meses=1)[0]
    assert mes["meta"] is None
    assert mes["depois_da_meta"] is None
    assert mes["variavel_estimado"] == 0


def test_semanas_restantes():
    assert semanas_restantes(11, 2026, date(2026, 11, 1)) == 5
    assert semanas_restantes(11, 2026, date(2026, 11, 24)) == 1
    assert semanas_restantes(10, 2026, date(2026, 11, 1)) == 0
    assert semanas_restantes(2, 2090, date(2026, 11, 1)) == 4
