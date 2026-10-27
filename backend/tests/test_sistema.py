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


def test_exportar_devolve_todas_as_tabelas(client):
    _transacao(client)
    dados = client.get("/api/exportar").json()
    assert "transacoes" in dados
    assert "cartoes" in dados
    assert len(dados["transacoes"]) == 1
    assert "_exportado_em" in dados


def test_exportar_inclui_listas_configuracoes_e_planos(client):
    client.put("/api/mes/2026/11/plano", json={"meta_valor": 500})
    dados = client.get("/api/exportar").json()
    for tabela in ("transacoes", "cartoes", "opcoes", "configuracoes", "planos_mes"):
        assert tabela in dados
    assert dados["planos_mes"][0]["meta_valor"] == 500
    assert any(o["chave"] == "salario" for o in dados["opcoes"])


def test_rota_de_encerrar_o_app_nao_existe(client):
    assert client.post("/api/sair").status_code in (404, 405)
