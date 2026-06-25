"""
Produto service: CRUD helpers used by the route layer.

Multi-tenant: TODA operação recebe `sistema_id` e filtra/insere no escopo
daquele sistema. SKU e categoria são validados dentro do sistema.
"""

import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.produto import Produto
from app.models.categoria import Categoria
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, ProdutoOut, ProdutoPaginado


def _enrich(produto: Produto) -> ProdutoOut:
    """Map ORM instance to ProdutoOut, adding denormalized name fields."""
    return ProdutoOut(
        id=produto.id,
        nome=produto.nome,
        sku=produto.sku,
        preco_custo=produto.preco_custo,
        preco_venda=produto.preco_venda,
        quantidade=produto.quantidade,
        qtd_minima=produto.qtd_minima,
        categoria_id=produto.categoria_id,
        categoria_nome=produto.categoria.nome if produto.categoria else None,
        fornecedor_id=produto.fornecedor_id,
        fornecedor_nome=produto.fornecedor.nome if produto.fornecedor else None,
        imagem_url=produto.imagem_url,
        criado_em=produto.criado_em,
        atualizado_em=produto.atualizado_em,
    )


def listar_produtos(
    db: Session,
    sistema_id: int,
    q: str | None,
    categoria_id: int | None,
    page: int,
    size: int,
) -> ProdutoPaginado:
    query = (
        db.query(Produto)
        .filter(Produto.sistema_id == sistema_id)
        .options(joinedload(Produto.categoria), joinedload(Produto.fornecedor))
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Produto.nome.ilike(like), Produto.sku.ilike(like)))

    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)

    total = query.count()
    pages = max(1, math.ceil(total / size))
    items = query.offset((page - 1) * size).limit(size).all()

    return ProdutoPaginado(
        items=[_enrich(p) for p in items],
        total=total,
        page=page,
        pages=pages,
    )


def obter_produto(db: Session, sistema_id: int, produto_id: int) -> ProdutoOut:
    produto = (
        db.query(Produto)
        .options(joinedload(Produto.categoria), joinedload(Produto.fornecedor))
        .filter(Produto.id == produto_id, Produto.sistema_id == sistema_id)
        .first()
    )
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return _enrich(produto)


def criar_produto(db: Session, sistema_id: int, dados: ProdutoCreate) -> ProdutoOut:
    # Categoria precisa existir DENTRO do sistema.
    cat = (
        db.query(Categoria)
        .filter(Categoria.id == dados.categoria_id, Categoria.sistema_id == sistema_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=422, detail="Categoria não encontrada")

    # SKU único dentro do sistema.
    if (
        db.query(Produto)
        .filter(Produto.sistema_id == sistema_id, Produto.sku == dados.sku)
        .first()
    ):
        raise HTTPException(status_code=422, detail=f"SKU '{dados.sku}' já está em uso")

    produto = Produto(sistema_id=sistema_id, **dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return obter_produto(db, sistema_id, produto.id)


def atualizar_produto(
    db: Session, sistema_id: int, produto_id: int, dados: ProdutoUpdate
) -> ProdutoOut:
    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id, Produto.sistema_id == sistema_id)
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    updates = dados.model_dump(exclude_unset=True)
    updates.pop("quantidade", None)  # quantidade nunca é setada aqui

    if "sku" in updates and updates["sku"] != produto.sku:
        if (
            db.query(Produto)
            .filter(Produto.sistema_id == sistema_id, Produto.sku == updates["sku"])
            .first()
        ):
            raise HTTPException(status_code=422, detail=f"SKU '{updates['sku']}' já está em uso")

    if "categoria_id" in updates:
        if (
            not db.query(Categoria)
            .filter(Categoria.id == updates["categoria_id"], Categoria.sistema_id == sistema_id)
            .first()
        ):
            raise HTTPException(status_code=422, detail="Categoria não encontrada")

    for field, value in updates.items():
        setattr(produto, field, value)

    db.commit()
    db.refresh(produto)
    return obter_produto(db, sistema_id, produto.id)


def deletar_produto(db: Session, sistema_id: int, produto_id: int) -> None:
    from app.models.movimentacao import Movimentacao

    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id, Produto.sistema_id == sistema_id)
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    tem_movimentacoes = (
        db.query(Movimentacao).filter(Movimentacao.produto_id == produto_id).first()
    )
    if tem_movimentacoes:
        raise HTTPException(
            status_code=409,
            detail="Não é possível excluir produto com movimentações registradas. "
                   "Desative o produto ou arquive-o.",
        )

    db.delete(produto)
    db.commit()
