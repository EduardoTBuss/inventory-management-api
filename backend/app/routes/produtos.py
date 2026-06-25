"""
Produtos routes (escopados por sistema).
GET endpoints: qualquer usuário do sistema.
POST/PUT/DELETE: admin do sistema.
quantidade NUNCA é atualizada por estas rotas.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, ProdutoOut, ProdutoPaginado
from app.services import produto_service
from app.auth.dependencies import require_admin, get_sistema_id

router = APIRouter()


@router.get("", response_model=ProdutoPaginado)
def listar_produtos(
    q: str | None = Query(default=None, description="Search by name or SKU"),
    categoria_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    return produto_service.listar_produtos(
        db, sistema_id, q=q, categoria_id=categoria_id, page=page, size=size
    )


@router.get("/{produto_id}", response_model=ProdutoOut)
def obter_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    return produto_service.obter_produto(db, sistema_id, produto_id)


@router.post("", response_model=ProdutoOut, status_code=201)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    return produto_service.criar_produto(db, sistema_id, dados)


@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    return produto_service.atualizar_produto(db, sistema_id, produto_id, dados)


@router.delete("/{produto_id}", status_code=204)
def deletar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    produto_service.deletar_produto(db, sistema_id, produto_id)
