"""
Dashboard route — aggregate statistics for the main screen, escopado por sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.movimentacao import Movimentacao
from app.schemas.produto import ProdutoResumo
from app.schemas.movimentacao import MovimentacaoOut
from app.auth.dependencies import get_sistema_id

router = APIRouter()


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    sistema_id: int = Depends(get_sistema_id),
):
    """KPIs agregados do sistema do usuário logado."""
    total_produtos = (
        db.query(func.count(Produto.id)).filter(Produto.sistema_id == sistema_id).scalar()
    )
    total_categorias = (
        db.query(func.count(Categoria.id)).filter(Categoria.sistema_id == sistema_id).scalar()
    )

    valor_total_estoque = (
        db.query(func.sum(Produto.preco_custo * Produto.quantidade))
        .filter(Produto.sistema_id == sistema_id)
        .scalar()
        or 0.0
    )

    abaixo = (
        db.query(Produto)
        .filter(Produto.sistema_id == sistema_id, Produto.quantidade < Produto.qtd_minima)
        .order_by(Produto.quantidade.asc())
        .all()
    )
    produtos_abaixo_minimo = [ProdutoResumo.model_validate(p) for p in abaixo]

    recentes_orm = (
        db.query(Movimentacao)
        .filter(Movimentacao.sistema_id == sistema_id)
        .options(joinedload(Movimentacao.produto), joinedload(Movimentacao.usuario))
        .order_by(Movimentacao.criado_em.desc())
        .limit(10)
        .all()
    )
    movimentacoes_recentes = [
        MovimentacaoOut(
            id=m.id,
            produto_id=m.produto_id,
            produto_nome=m.produto.nome if m.produto else None,
            tipo=m.tipo,
            quantidade=m.quantidade,
            motivo=m.motivo,
            usuario_id=m.usuario_id,
            usuario_nome=m.usuario.nome if m.usuario else None,
            criado_em=m.criado_em,
        )
        for m in recentes_orm
    ]

    mais_movimentados_raw = (
        db.query(Produto.nome, func.count(Movimentacao.id).label("total"))
        .join(Movimentacao, Movimentacao.produto_id == Produto.id)
        .filter(Produto.sistema_id == sistema_id)
        .group_by(Produto.id, Produto.nome)
        .order_by(func.count(Movimentacao.id).desc())
        .limit(5)
        .all()
    )
    mais_movimentados = [
        {"produto_nome": row.nome, "total_movimentacoes": row.total}
        for row in mais_movimentados_raw
    ]

    return {
        "total_produtos": total_produtos,
        "total_categorias": total_categorias,
        "valor_total_estoque": round(float(valor_total_estoque), 2),
        "produtos_abaixo_minimo": produtos_abaixo_minimo,
        "movimentacoes_recentes": movimentacoes_recentes,
        "mais_movimentados": mais_movimentados,
    }
