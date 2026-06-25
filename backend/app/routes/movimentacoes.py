"""
Movimentacoes routes (escopadas por sistema).
GET e POST exigem autenticação. POST é liberado a qualquer usuário do sistema
(operadores podem registrar movimentações).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.movimentacao import MovimentacaoCreate, MovimentacaoOut, MovimentacaoPaginada
from app.services import movimentacao_service
from app.auth.dependencies import get_current_user, get_sistema_id
from app.models.usuario import Usuario

router = APIRouter()


@router.get("", response_model=MovimentacaoPaginada)
def listar_movimentacoes(
    produto_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None, description="entrada | saida | ajuste"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    return movimentacao_service.listar_movimentacoes(
        db, sistema_id, produto_id=produto_id, tipo=tipo, page=page, size=size
    )


@router.post("", response_model=MovimentacaoOut, status_code=201)
def registrar_movimentacao(
    dados: MovimentacaoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    sistema_id: int = Depends(get_sistema_id),
):
    return movimentacao_service.registrar_movimentacao(db, sistema_id, dados, current_user.id)
