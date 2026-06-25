"""
Movimentacao service — the core of the event-sourcing-lite architecture.

INVARIANT: produto.quantidade == SUM(delta for each movimentacao)
  where delta = +quantidade for "entrada"/"ajuste"
               -quantidade for "saida"

Multi-tenant: toda operação é escopada por sistema_id. O produto precisa
pertencer ao sistema do usuário, e a movimentação registra o mesmo sistema_id.

Every stock change is performed inside a single DB transaction:
  1. Lock the product row (with_for_update → serialised in SQLite)
  2. Apply the delta
  3. Insert the movimentacao record
  4. Commit atomically
"""

import math
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.produto import Produto
from app.models.movimentacao import Movimentacao, TipoMovimentacaoEnum
from app.schemas.movimentacao import MovimentacaoCreate, MovimentacaoOut, MovimentacaoPaginada


def _enrich(mov: Movimentacao) -> MovimentacaoOut:
    return MovimentacaoOut(
        id=mov.id,
        produto_id=mov.produto_id,
        produto_nome=mov.produto.nome if mov.produto else None,
        tipo=mov.tipo,
        quantidade=mov.quantidade,
        motivo=mov.motivo,
        usuario_id=mov.usuario_id,
        usuario_nome=mov.usuario.nome if mov.usuario else None,
        criado_em=mov.criado_em,
    )


def registrar_movimentacao(
    db: Session,
    sistema_id: int,
    dados: MovimentacaoCreate,
    usuario_id: int,
) -> MovimentacaoOut:
    """
    Register a stock movement transactionally, dentro do sistema informado.

    Raises:
        404 — produto não encontrado no sistema
        422 — saida que resultaria em estoque negativo
    """
    try:
        produto = db.execute(
            select(Produto)
            .where(Produto.id == dados.produto_id, Produto.sistema_id == sistema_id)
            .with_for_update()
        ).scalar_one_or_none()

        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        if dados.tipo == TipoMovimentacaoEnum.saida:
            if produto.quantidade < dados.quantidade:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Estoque insuficiente: disponível {produto.quantidade}, "
                        f"solicitado {dados.quantidade}"
                    ),
                )
            delta = -dados.quantidade
        else:
            delta = dados.quantidade

        produto.quantidade += delta
        produto.atualizado_em = datetime.utcnow()

        mov = Movimentacao(
            sistema_id=sistema_id,
            produto_id=dados.produto_id,
            tipo=dados.tipo,
            quantidade=dados.quantidade,
            motivo=dados.motivo,
            usuario_id=usuario_id,
        )
        db.add(mov)
        db.flush()
        db.commit()
        db.refresh(mov)

        mov_com_nomes = (
            db.query(Movimentacao).filter(Movimentacao.id == mov.id).first()
        )
        return _enrich(mov_com_nomes)

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def listar_movimentacoes(
    db: Session,
    sistema_id: int,
    produto_id: int | None,
    tipo: str | None,
    page: int,
    size: int,
) -> MovimentacaoPaginada:
    """Movimentações paginadas DO SISTEMA, filtráveis por produto e/ou tipo."""
    from sqlalchemy.orm import joinedload

    query = (
        db.query(Movimentacao)
        .filter(Movimentacao.sistema_id == sistema_id)
        .options(joinedload(Movimentacao.produto), joinedload(Movimentacao.usuario))
        .order_by(Movimentacao.criado_em.desc())
    )

    if produto_id:
        query = query.filter(Movimentacao.produto_id == produto_id)

    if tipo:
        try:
            tipo_enum = TipoMovimentacaoEnum(tipo)
            query = query.filter(Movimentacao.tipo == tipo_enum)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Tipo inválido: '{tipo}'. Use entrada, saida ou ajuste.",
            )

    total = query.count()
    pages = max(1, math.ceil(total / size))
    items = query.offset((page - 1) * size).limit(size).all()

    return MovimentacaoPaginada(
        items=[_enrich(m) for m in items],
        total=total,
        page=page,
        pages=pages,
    )
