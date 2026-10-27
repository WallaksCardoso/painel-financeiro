from datetime import date

import pytest

from app.services.opcoes import semear


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


def test_semear_cria_padroes_e_inclui_chaves_ja_usadas(client, db_session):

    from app.models import Transacao

    db_session.add(
        Transacao(
            lancamento="Ração", tipo="despesa", categoria="pet", valor=50, data=date(2026, 11, 5)
        )
    )
    db_session.commit()
    semear(db_session)
    categorias = {o["chave"]: o["nome"] for o in client.get("/api/opcoes?grupo=categoria").json()}
    assert categorias["salario"] == "Salário"
    assert categorias["pet"] == "Pet"
    semear(db_session)
    assert len(client.get("/api/opcoes?grupo=categoria").json()) == len(categorias)


def test_criar_renomear_e_apagar_opcao(client):
    antes = len(client.get("/api/opcoes?grupo=categoria").json())
    r = client.post("/api/opcoes", json={"grupo": "categoria", "nome": "  Viagem de Férias "})
    assert r.status_code == 201
    opcao = r.json()
    assert (opcao["nome"], opcao["chave"]) == ("Viagem de Férias", "viagem_de_ferias")
    assert (
        client.post(
            "/api/opcoes", json={"grupo": "categoria", "nome": "Viagem de Férias"}
        ).status_code
        == 409
    )
    assert client.post("/api/opcoes", json={"grupo": "categoria", "nome": "   "}).status_code == 422

    r = client.patch(f"/api/opcoes/{opcao['id']}", json={"nome": "Sítio"})
    assert (r.json()["nome"], r.json()["chave"]) == ("Sítio", "viagem_de_ferias")
    assert client.patch(f"/api/opcoes/{opcao['id']}", json={"nome": "Lazer"}).status_code == 409

    assert client.delete(f"/api/opcoes/{opcao['id']}").status_code == 204
    assert len(client.get("/api/opcoes?grupo=categoria").json()) == antes


@pytest.mark.parametrize(
    "grupo,criar",
    [
        ("categoria", lambda c: _transacao(c, categoria="pet")),
        ("meio_pagamento", lambda c: _transacao(c, meio_pagamento="pet")),
    ],
)
def test_opcao_em_uso_nao_pode_ser_apagada(client, grupo, criar):
    opcao = client.post("/api/opcoes", json={"grupo": grupo, "nome": "Pet"}).json()
    assert opcao["chave"] == "pet"
    criar(client)
    r = client.delete(f"/api/opcoes/{opcao['id']}")
    assert r.status_code == 409
    assert "em uso" in r.json()["detail"]


def test_grupo_invalido_e_recusado(client):
    assert client.post("/api/opcoes", json={"grupo": "xpto", "nome": "A"}).status_code == 422


def test_semear_grava_meta_da_reserva_so_uma_vez(client, db_session):
    semear(db_session)
    assert client.get("/api/config/meta_reserva").json()["valor"] == "8000"
    client.put("/api/config/meta_reserva", json={"valor": "12000"})
    semear(db_session)
    assert client.get("/api/config/meta_reserva").json()["valor"] == "12000"


def test_configuracao_salva_e_valida(client):
    assert client.get("/api/config/meta_reserva").json()["valor"] == "8000"
    assert (
        client.put("/api/config/meta_reserva", json={"valor": "10000,50"}).json()["valor"]
        == "10000.5"
    )
    assert client.put("/api/config/meta_reserva", json={"valor": "abc"}).status_code == 422
    assert client.put("/api/config/meta_reserva", json={"valor": "-5"}).status_code == 422
    assert client.put("/api/config/dias_proximas_contas", json={"valor": "7.5"}).status_code == 422
    assert client.put("/api/config/inventada", json={"valor": "1"}).status_code == 404
    assert client.get("/api/config/meta_reserva").json()["valor"] == "10000.5"


def test_opcao_duplicada_sem_diferenciar_maiuscula_ou_acento(client):
    assert (
        client.post("/api/opcoes", json={"grupo": "categoria", "nome": "moradia"}).status_code
        == 409
    )
    assert (
        client.post("/api/opcoes", json={"grupo": "categoria", "nome": "Saude"}).status_code == 409
    )


def test_mensagens_em_portugues(client):
    r = _lancamento_eventual(client, meio_pagamento="cheque")
    assert "não está cadastrado" in r.json()["detail"]
    r = client.put("/api/config/meta_reserva", json={"valor": "-1"})
    assert "100.000.000" in r.json()["detail"]
