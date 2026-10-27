def _movimento(client, tipo, valor):
    return client.post(
        "/api/reserva",
        json={"descricao": tipo, "tipo": tipo, "valor": valor, "data": "2026-05-10"},
    )


def _mov(client, **kwargs):
    base = {
        "descricao": "x",
        "tipo": "aporte",
        "valor": 100.0,
        "data": "2026-05-10",
        "origem": "salario",
        "observacao": None,
    }
    base.update(kwargs)
    return client.post("/api/reserva", json=base)


def test_nao_apaga_aporte_que_deixaria_reserva_negativa(client):
    aporte = _movimento(client, "aporte", 100).json()
    _movimento(client, "saque", 80)
    r = client.delete(f"/api/reserva/{aporte['id']}")
    assert r.status_code == 400
    assert client.get("/api/reserva/saldo").json()["saldo"] == 20


def test_reserva_com_tipo_invalido_e_recusada(client):
    assert _movimento(client, "transferencia", 10).status_code == 422


def test_saque_maior_que_saldo_e_bloqueado(client):
    _mov(client, tipo="aporte", valor=100)
    r = _mov(client, tipo="saque", valor=150)
    assert r.status_code == 400
    assert client.get("/api/reserva/saldo").json()["saldo"] == 100


def test_saque_dentro_do_saldo_passa(client):
    _mov(client, tipo="aporte", valor=100)
    r = _mov(client, tipo="saque", valor=60)
    assert r.status_code == 201
    assert client.get("/api/reserva/saldo").json()["saldo"] == 40


def test_reserva_com_origem_inexistente_e_recusada(client):
    r = client.post(
        "/api/reserva",
        json={
            "descricao": "X",
            "tipo": "aporte",
            "valor": 5,
            "data": "2026-10-01",
            "origem": "xyz",
        },
    )
    assert r.status_code == 422


def test_saque_retroativo_que_deixaria_historico_negativo_e_recusado(client):
    mov = {"descricao": "X", "origem": "salario"}
    client.post("/api/reserva", json={**mov, "tipo": "aporte", "valor": 1000, "data": "2026-10-20"})
    r = client.post(
        "/api/reserva", json={**mov, "tipo": "saque", "valor": 500, "data": "2026-10-01"}
    )
    assert r.status_code == 400
    assert "01/10/2026" in r.json()["detail"]
    assert (
        client.post(
            "/api/reserva", json={**mov, "tipo": "saque", "valor": 500, "data": "2026-10-20"}
        ).status_code
        == 201
    )


def test_editar_movimento_da_reserva(client):
    a = client.post(
        "/api/reserva",
        json={"descricao": "Aporte", "tipo": "aporte", "valor": 100, "data": "2026-10-01"},
    ).json()
    client.post(
        "/api/reserva",
        json={"descricao": "Saque", "tipo": "saque", "valor": 80, "data": "2026-10-10"},
    )
    assert client.patch(f"/api/reserva/{a['id']}", json={"valor": 50}).status_code == 400
    r = client.patch(f"/api/reserva/{a['id']}", json={"valor": 120, "descricao": "Aporte maior"})
    assert r.status_code == 200 and r.json()["valor"] == 120
    assert client.get("/api/reserva/saldo").json()["saldo"] == 40
