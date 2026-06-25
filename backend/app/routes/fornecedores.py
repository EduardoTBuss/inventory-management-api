"""
Fornecedores routes — full CRUD, escopado por sistema.
GET: qualquer usuário do sistema. POST/PUT/DELETE: admin do sistema.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fornecedor import Fornecedor
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate, FornecedorOut
from app.auth.dependencies import require_admin, get_sistema_id

router = APIRouter()


@router.get("", response_model=list[FornecedorOut])
def listar_fornecedores(
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    return (
        db.query(Fornecedor)
        .filter(Fornecedor.sistema_id == sistema_id)
        .order_by(Fornecedor.nome)
        .all()
    )


@router.post("", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(
    dados: FornecedorCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    forn = Fornecedor(sistema_id=sistema_id, **dados.model_dump())
    db.add(forn)
    db.commit()
    db.refresh(forn)
    return forn


@router.put("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar_fornecedor(
    fornecedor_id: int,
    dados: FornecedorUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    forn = (
        db.query(Fornecedor)
        .filter(Fornecedor.id == fornecedor_id, Fornecedor.sistema_id == sistema_id)
        .first()
    )
    if not forn:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    for field, value in dados.model_dump(exclude_unset=True).items():
        setattr(forn, field, value)

    db.commit()
    db.refresh(forn)
    return forn


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    from app.models.produto import Produto

    forn = (
        db.query(Fornecedor)
        .filter(Fornecedor.id == fornecedor_id, Fornecedor.sistema_id == sistema_id)
        .first()
    )
    if not forn:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

    tem_produtos = (
        db.query(Produto)
        .filter(Produto.fornecedor_id == fornecedor_id, Produto.sistema_id == sistema_id)
        .first()
    )
    if tem_produtos:
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir fornecedor com produtos vinculados. "
                   "Desvincule os produtos primeiro.",
        )

    db.delete(forn)
    db.commit()
