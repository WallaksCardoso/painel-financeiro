from datetime import date

import pytest

from app.services.fatura import valores_parcelas as _valores_parcelas


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


def _fatura(client, cartao_id, mes, ano):
    return client.get(f"/api/cartoes/{cartao_id}/fatura", params={"mes": mes, "ano": ano}).json()


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


def _cartao_completo(client, dia_fechamento=25, dia_vencimento=5):
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


def _cartao_simples(client, fecha=8, vence=15, nome="Cartão X"):
    r = client.post(
        "/api/cartoes", json={"nome": nome, "dia_fechamento": fecha, "dia_vencimento": vence}
    )
    return r.json()


def _mes(client, mes, ano=2026):
    return client.get(f"/api/mes/{ano}/{mes}").json()


def test_vencimento_cai_no_mes_seguinte_quando_vence_antes_do_fechamento(client):
    cartao = _cartao(client, dia_fechamento=25, dia_vencimento=5)
    assert _fatura(client, cartao["id"], 5, 2026)["vencimento"] == "2026-06-05"


def test_vencimento_no_mesmo_mes_quando_vence_depois_do_fechamento(client):
    cartao = _cartao(client, dia_fechamento=3, dia_vencimento=10)
    assert _fatura(client, cartao["id"], 5, 2026)["vencimento"] == "2026-05-10"


def test_vencimento_de_dezembro_vira_o_ano(client):
    cartao = _cartao(client, dia_fechamento=25, dia_vencimento=5)
    assert _fatura(client, cartao["id"], 12, 2026)["vencimento"] == "2027-01-05"


@pytest.mark.parametrize("total,n", [(1, 60), (0.10, 12), (100, 3), (100, 60), (999.99, 7)])
def test_parcelas_somam_o_total_e_nunca_sao_negativas(total, n):
    valores = _valores_parcelas(total, n)
    assert len(valores) == n
    assert round(sum(valores), 2) == round(total, 2)
    assert min(valores) >= 0
    assert round(max(valores) - min(valores), 2) <= 0.01


def test_centavos_que_sobram_vao_para_as_ultimas_parcelas():
    assert _valores_parcelas(100, 3) == [33.33, 33.33, 33.34]


def test_cartao_novo_nao_herda_fatura_paga_de_cartao_apagado(client):
    antigo = _cartao(client)
    client.post(f"/api/cartoes/{antigo['id']}/faturas", json={"mes": 6, "ano": 2026})
    client.delete(f"/api/cartoes/{antigo['id']}")
    novo = _cartao(client)
    assert _fatura(client, novo["id"], 6, 2026)["pago"] is False


def test_compra_a_vista_antes_do_fechamento_cai_no_mesmo_mes(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-05-10", valor_total=200, parcelas=1)

    fatura = _fatura(client, cartao["id"], 5, 2026)
    assert fatura["total"] == 200.0
    assert len(fatura["itens"]) == 1


def test_compra_apos_fechamento_cai_no_mes_seguinte(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-05-26", valor_total=200, parcelas=1)

    assert _fatura(client, cartao["id"], 5, 2026)["total"] == 0.0
    assert _fatura(client, cartao["id"], 6, 2026)["total"] == 200.0


def test_compra_parcelada_distribui_em_meses_consecutivos(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-05-10", valor_total=300, parcelas=3)

    f5 = _fatura(client, cartao["id"], 5, 2026)
    f6 = _fatura(client, cartao["id"], 6, 2026)
    f7 = _fatura(client, cartao["id"], 7, 2026)
    f8 = _fatura(client, cartao["id"], 8, 2026)

    assert f5["total"] == 100.0
    assert f6["total"] == 100.0
    assert f7["total"] == 100.0
    assert f8["total"] == 0.0

    item = f5["itens"][0]
    assert item["parcela_atual"] == 1
    assert item["parcelas_restantes"] == 2

    item7 = f7["itens"][0]
    assert item7["parcela_atual"] == 3
    assert item7["parcelas_restantes"] == 0


def test_parcelamento_cruza_o_ano(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-12-10", valor_total=600, parcelas=3)

    assert _fatura(client, cartao["id"], 12, 2026)["total"] == 200.0
    assert _fatura(client, cartao["id"], 1, 2027)["total"] == 200.0
    assert _fatura(client, cartao["id"], 2, 2027)["total"] == 200.0


def test_fatura_separa_fixos_e_variaveis(client):
    cartao = _cartao(client)
    _compra(client, cartao["id"], descricao="Spotify", valor_total=21.90, recorrente=True)
    _compra(client, cartao["id"], descricao="Padaria", valor_total=50.0, recorrente=False)

    fatura = _fatura(client, cartao["id"], 5, 2026)
    assert fatura["total_fixo"] == 21.90
    assert fatura["total_variavel"] == 50.0
    assert fatura["total"] == 71.90


def test_total_comprometido_futuro_ignora_recorrentes(client):
    cartao = _cartao(client)
    _compra(client, cartao["id"], valor_total=400, parcelas=4, recorrente=False)
    _compra(client, cartao["id"], valor_total=21.90, parcelas=1, recorrente=True)

    fatura = _fatura(client, cartao["id"], 5, 2026)
    assert fatura["total_comprometido_futuro"] == 300.0


def test_dia_vencimento_invalido_ajusta_fim_do_mes(client):
    cartao = _cartao(client, dia_fechamento=20, dia_vencimento=31)
    fatura = _fatura(client, cartao["id"], 2, 2026)
    assert fatura["vencimento"] == "2026-02-28"


def test_recorrente_se_repete_nas_faturas_seguintes(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(
        client,
        cartao["id"],
        descricao="Spotify",
        valor_total=21.90,
        data_compra="2026-05-10",
        recorrente=True,
    )

    assert _fatura(client, cartao["id"], 4, 2026)["total"] == 0.0
    for mes, ano in [(5, 2026), (6, 2026), (12, 2026), (1, 2027)]:
        fatura = _fatura(client, cartao["id"], mes, ano)
        assert fatura["total"] == 21.90
        assert fatura["total_fixo"] == 21.90
        assert fatura["itens"][0]["parcela_atual"] == 1
        assert fatura["itens"][0]["parcelas_restantes"] == 0


def test_recorrente_apos_fechamento_comeca_no_mes_seguinte(client):
    cartao = _cartao(client, dia_fechamento=25)
    _compra(client, cartao["id"], valor_total=50.0, data_compra="2026-05-26", recorrente=True)

    assert _fatura(client, cartao["id"], 5, 2026)["total"] == 0.0
    assert _fatura(client, cartao["id"], 6, 2026)["total"] == 50.0
    assert _fatura(client, cartao["id"], 7, 2026)["total"] == 50.0


def test_fatura_nasce_aberta(client):
    cartao = _setup_cartao_e_compra(client)
    f = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 5, "ano": 2026}).json()
    assert f["pago"] is False
    assert f["pago_em"] is None
    assert f["fatura_paga_id"] is None


def test_marcar_fatura_paga(client):
    cartao = _setup_cartao_e_compra(client)
    r = client.post(
        f"/api/cartoes/{cartao['id']}/faturas",
        json={"mes": 5, "ano": 2026, "pago_em": "2026-06-05", "valor_pago": 200.0},
    )
    assert r.status_code == 201

    f = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 5, "ano": 2026}).json()
    assert f["pago"] is True
    assert f["pago_em"] == "2026-06-05"
    assert f["valor_pago"] == 200.0


def test_nao_marca_duas_vezes_a_mesma_fatura(client):
    cartao = _setup_cartao_e_compra(client)
    client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 5, "ano": 2026})
    r = client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 5, "ano": 2026})
    assert r.status_code == 409


def test_desmarcar_fatura(client):
    cartao = _setup_cartao_e_compra(client)
    paga = client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 5, "ano": 2026}).json()
    assert client.delete(f"/api/cartoes/faturas/{paga['id']}").status_code == 204

    f = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 5, "ano": 2026}).json()
    assert f["pago"] is False


def test_marcar_paga_em_cartao_inexistente_da_404(client):
    r = client.post("/api/cartoes/9999/faturas", json={"mes": 5, "ano": 2026})
    assert r.status_code == 404


def test_pago_em_default_eh_hoje(client):
    cartao = _setup_cartao_e_compra(client)
    r = client.post(f"/api/cartoes/{cartao['id']}/faturas", json={"mes": 5, "ano": 2026}).json()
    assert r["pago_em"] == date.today().isoformat()


def test_parcela_fecha_o_centavo_na_ultima(client):
    cartao = _cartao_completo(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-05-10", valor_total=100, parcelas=3)

    f5 = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 5, "ano": 2026}).json()
    f6 = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 6, "ano": 2026}).json()
    f7 = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 7, "ano": 2026}).json()

    assert f5["total"] == 33.33
    assert f6["total"] == 33.33
    assert f7["total"] == 33.34
    assert round(f5["total"] + f6["total"] + f7["total"], 2) == 100.0


def test_comprometido_futuro_soma_parcelas_reais(client):
    cartao = _cartao_completo(client, dia_fechamento=25)
    _compra(client, cartao["id"], data_compra="2026-05-10", valor_total=100, parcelas=3)
    f5 = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 5, "ano": 2026}).json()
    assert f5["total_comprometido_futuro"] == 66.67


def test_fatura_pelo_mes_do_vencimento(client):
    cartao = _cartao_simples(client, fecha=28, vence=5)
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": cartao["id"],
            "descricao": "X",
            "valor_total": 90,
            "parcelas": 3,
            "data_compra": "2026-11-20",
        },
    )
    f = client.get(
        f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 12, "ano": 2026, "vence_em": True}
    ).json()
    assert (f["mes"], f["ano"], f["vencimento"], f["total"]) == (11, 2026, "2026-12-05", 30)


def test_parcelas_contam_como_fixas_na_fatura(client):
    cartao = _cartao_simples(client)
    base = {"cartao_id": cartao["id"], "data_compra": "2026-11-01"}
    client.post(
        "/api/cartoes/compras",
        json={**base, "descricao": "Netflix", "valor_total": 20, "recorrente": True},
    )
    client.post(
        "/api/cartoes/compras",
        json={**base, "descricao": "Fone", "valor_total": 300, "parcelas": 3},
    )
    client.post("/api/cartoes/compras", json={**base, "descricao": "Mercado", "valor_total": 50})
    f = client.get(f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 11, "ano": 2026}).json()
    assert (f["total_fixo"], f["total_variavel"]) == (120, 50)
    assert _mes(client, 11)["cartao_variavel"] == 50


def test_comprometido_futuro_inclui_compra_que_ainda_nao_comecou(client):
    c = client.post(
        "/api/cartoes", json={"nome": "Cartão X", "dia_fechamento": 8, "dia_vencimento": 15}
    ).json()
    client.post(
        "/api/cartoes/compras",
        json={
            "cartao_id": c["id"],
            "descricao": "Plano anual",
            "valor_total": 240,
            "parcelas": 12,
            "data_compra": "2026-10-18",
        },
    )
    out = client.get(f"/api/cartoes/{c['id']}/fatura?mes=10&ano=2026").json()
    assert out["total_comprometido_futuro"] == 240


def test_fatura_paga_com_valor_negativo_e_recusada(client):
    c = client.post(
        "/api/cartoes", json={"nome": "Cartão X", "dia_fechamento": 8, "dia_vencimento": 15}
    ).json()
    r = client.post(
        f"/api/cartoes/{c['id']}/faturas", json={"mes": 10, "ano": 2026, "valor_pago": -10}
    )
    assert r.status_code == 422
