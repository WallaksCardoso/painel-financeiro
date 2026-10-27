from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from ..database import Db
from ..models import Configuracao, Opcao
from ..schemas import (
    ConfiguracaoIn,
    ConfiguracaoOut,
    GrupoOpcao,
    OpcaoCreate,
    OpcaoOut,
    OpcaoUpdate,
)
from ..services import opcoes as svc
from ._comum import formatar_numero, obter_ou_404

router = APIRouter(prefix="/api", tags=["opcoes"])


@router.get("/opcoes", response_model=list[OpcaoOut])
def listar(db: Db, grupo: Annotated[GrupoOpcao | None, Query()] = None):
    query = db.query(Opcao)
    if grupo is not None:
        query = query.filter(Opcao.grupo == grupo)
    return query.order_by(Opcao.grupo, Opcao.ordem, Opcao.nome).all()


@router.post("/opcoes", response_model=OpcaoOut, status_code=201)
def criar(db: Db, payload: OpcaoCreate):
    nome = payload.nome
    repetida = svc.nome_repetido(db, payload.grupo, nome)
    if repetida:
        raise HTTPException(status_code=409, detail=f'Já existe "{repetida.nome}" nesta lista')
    ultima = db.query(Opcao).filter(Opcao.grupo == payload.grupo).count()
    opcao = Opcao(
        grupo=payload.grupo,
        chave=svc.chave_livre(db, payload.grupo, nome),
        nome=nome,
        ordem=ultima,
    )
    db.add(opcao)
    db.commit()
    db.refresh(opcao)
    return opcao


@router.patch("/opcoes/{opcao_id}", response_model=OpcaoOut)
def atualizar(db: Db, opcao_id: int, payload: OpcaoUpdate):
    opcao = obter_ou_404(db, Opcao, opcao_id, "Opção não encontrada")
    dados = payload.model_dump(exclude_unset=True)
    if "nome" in dados:
        repetida = svc.nome_repetido(db, opcao.grupo, dados["nome"], ignorar_id=opcao.id)
        if repetida:
            raise HTTPException(status_code=409, detail=f'Já existe "{repetida.nome}" nesta lista')
    for campo, valor in dados.items():
        setattr(opcao, campo, valor)
    db.commit()
    db.refresh(opcao)
    return opcao


@router.delete("/opcoes/{opcao_id}", status_code=204)
def remover(db: Db, opcao_id: int):
    opcao = obter_ou_404(db, Opcao, opcao_id, "Opção não encontrada")
    em_uso = svc.usos(db, opcao)
    if em_uso:
        raise HTTPException(
            status_code=409,
            detail=f'"{opcao.nome}" está em uso em {em_uso} registro(s). '
            "Troque esses registros para outra opção antes de apagar, ou só renomeie.",
        )
    db.delete(opcao)
    db.commit()


@router.get("/config/{chave}", response_model=ConfiguracaoOut)
def ler_config(db: Db, chave: str):
    item = db.get(Configuracao, chave)
    return ConfiguracaoOut(chave=chave, valor=item.valor if item else None)


@router.put("/config/{chave}", response_model=ConfiguracaoOut)
def salvar_config(db: Db, chave: str, payload: ConfiguracaoIn):
    regra = svc.CONFIGURACOES.get(chave)
    if regra is None:
        raise HTTPException(status_code=404, detail="Configuração desconhecida")
    minimo, maximo, inteiro = regra
    try:
        numero = float(payload.valor.replace(",", "."))
    except ValueError as erro:
        raise HTTPException(status_code=422, detail="Informe um número") from erro
    if not (minimo <= numero <= maximo) or (inteiro and not numero.is_integer()):
        faixa = f"entre {formatar_numero(minimo)} e {formatar_numero(maximo)}"
        raise HTTPException(
            status_code=422,
            detail=f"Valor deve ser {'um número inteiro ' if inteiro else ''}{faixa}",
        )
    texto = f"{int(numero)}" if inteiro else f"{numero:.2f}".rstrip("0").rstrip(".")
    payload = ConfiguracaoIn(valor=texto)
    item = db.get(Configuracao, chave)
    if item is None:
        item = Configuracao(chave=chave, valor=payload.valor)
        db.add(item)
    else:
        item.valor = payload.valor
    db.commit()
    return ConfiguracaoOut(chave=chave, valor=item.valor)
