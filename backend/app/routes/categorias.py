"""
Categorias routes — full CRUD, escopado por sistema.
GET: qualquer usuário do sistema. POST/PUT/DELETE: admin do sistema.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaOut
from app.auth.dependencies import require_admin, get_sistema_id

router = APIRouter()


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    return (
        db.query(Categoria)
        .filter(Categoria.sistema_id == sistema_id)
        .order_by(Categoria.nome)
        .all()
    )


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    if (
        db.query(Categoria)
        .filter(Categoria.sistema_id == sistema_id, Categoria.nome == dados.nome)
        .first()
    ):
        raise HTTPException(status_code=422, detail=f"Categoria '{dados.nome}' já existe")

    cat = Categoria(sistema_id=sistema_id, **dados.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(
    categoria_id: int,
    dados: CategoriaUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    cat = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id, Categoria.sistema_id == sistema_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    updates = dados.model_dump(exclude_unset=True)

    if "nome" in updates and updates["nome"] != cat.nome:
        if (
            db.query(Categoria)
            .filter(Categoria.sistema_id == sistema_id, Categoria.nome == updates["nome"])
            .first()
        ):
            raise HTTPException(status_code=422, detail=f"Nome '{updates['nome']}' já está em uso")

    for field, value in updates.items():
        setattr(cat, field, value)

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    cat = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id, Categoria.sistema_id == sistema_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    if cat.produtos:
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir categoria com produtos vinculados",
        )

    db.delete(cat)
    db.commit()
