from datetime import date

from app.demo import popular


def test_dados_de_demonstracao_montam_todas_as_telas(client, db_session):
    popular(db_session, hoje=date(2026, 11, 15))

    mes = client.get("/api/mes/2026/11").json()
    assert mes["total_receitas"] == 5300
    assert mes["total_beneficios"] == 900
    assert mes["plano"]["salvo"] is True

    fluxo = client.get("/api/projecao", params={"mes": 11, "ano": 2026, "meses": 6}).json()
    assert len(fluxo["meses"]) == 6
    assert fluxo["parcelas_ativas"]

    painel = client.get("/api/dashboard/completo", params={"mes": 11, "ano": 2026}).json()
    assert painel["saldo_reserva"] == 3300
    assert painel["total_dividas_restante"] == 4800 - 1200 - 800

    cartao = client.get("/api/cartoes").json()[0]
    fatura = client.get(
        f"/api/cartoes/{cartao['id']}/fatura", params={"mes": 11, "ano": 2026, "vence_em": True}
    ).json()
    assert fatura["total"] > 0
    assert client.get("/api/orcamento", params={"mes": 11, "ano": 2026}).json()
