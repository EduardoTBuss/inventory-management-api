"""
Rota de Funcionários/Equipe — ACESSO RESTRITO A ADMIN (require_admin → 403),
escopada ao sistema do admin logado.

  GET    /api/funcionarios        → estatísticas da equipe DO SISTEMA
  POST   /api/funcionarios        → cria um operador no sistema
  DELETE /api/funcionarios/{id}   → remove um operador do sistema
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.usuario import Usuario, PapelEnum
from app.models.produto import Produto
from app.models.movimentacao import Movimentacao, TipoMovimentacaoEnum
from app.schemas.funcionario import FuncionarioStats, EquipeOut, OperadorCreate
from app.schemas.usuario import UsuarioOut
from app.services.auth_service import hash_password
from app.auth.dependencies import require_admin, get_sistema_id

router = APIRouter()


@router.get("", response_model=EquipeOut)
def listar_equipe(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    """Estatísticas de cada funcionário DO SISTEMA. Somente admin."""
    vendas_raw = (
        db.query(
            Movimentacao.usuario_id.label("uid"),
            func.coalesce(func.sum(Movimentacao.quantidade), 0).label("unidades"),
            func.coalesce(
                func.sum(Movimentacao.quantidade * Produto.preco_venda), 0.0
            ).label("faturado"),
        )
        .join(Produto, Produto.id == Movimentacao.produto_id)
        .filter(
            Movimentacao.tipo == TipoMovimentacaoEnum.saida,
            Movimentacao.sistema_id == sistema_id,
        )
        .group_by(Movimentacao.usuario_id)
        .all()
    )
    vendas_por_uid = {
        row.uid: (int(row.unidades or 0), float(row.faturado or 0.0))
        for row in vendas_raw
    }

    atividade_raw = (
        db.query(
            Movimentacao.usuario_id.label("uid"),
            func.count(Movimentacao.id).label("qtd"),
            func.max(Movimentacao.criado_em).label("ultima"),
        )
        .filter(Movimentacao.sistema_id == sistema_id)
        .group_by(Movimentacao.usuario_id)
        .all()
    )
    atividade_por_uid = {
        row.uid: (int(row.qtd or 0), row.ultima) for row in atividade_raw
    }

    usuarios = (
        db.query(Usuario)
        .filter(Usuario.sistema_id == sistema_id)
        .all()
    )
    funcionarios: list[FuncionarioStats] = []
    for u in usuarios:
        unidades, faturado = vendas_por_uid.get(u.id, (0, 0.0))
        total_mov, ultima = atividade_por_uid.get(u.id, (0, None))
        funcionarios.append(
            FuncionarioStats(
                id=u.id,
                nome=u.nome,
                username=u.username,
                email=u.email,
                papel=u.papel,
                ativo=u.ativo,
                total_vendido=unidades,
                total_faturado=round(faturado, 2),
                total_movimentacoes=total_mov,
                ultima_atividade=ultima,
            )
        )

    funcionarios.sort(key=lambda f: (-f.total_faturado, f.nome.lower()))
    return EquipeOut(funcionarios=funcionarios, total_funcionarios=len(funcionarios))


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_operador(
    dados: OperadorCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    """Cria um operador no sistema do admin logado."""
    existe = (
        db.query(Usuario)
        .filter(Usuario.sistema_id == sistema_id, Usuario.username == dados.username)
        .first()
    )
    if existe:
        raise HTTPException(
            status_code=422,
            detail=f"Já existe um usuário '{dados.username}' neste sistema",
        )

    operador = Usuario(
        sistema_id=sistema_id,
        nome=dados.nome.strip(),
        username=dados.username,
        email=None,
        senha_hash=hash_password(dados.senha),
        papel=PapelEnum.operador,
        ativo=True,
    )
    db.add(operador)
    db.commit()
    db.refresh(operador)
    return operador


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_operador(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
    sistema_id: int = Depends(get_sistema_id),
):
    """Remove um operador do sistema. Não permite remover admins nem a si mesmo."""
    alvo = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id, Usuario.sistema_id == sistema_id)
        .first()
    )
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado neste sistema")
    if alvo.id == current_user.id:
        raise HTTPException(status_code=409, detail="Você não pode remover a si mesmo")
    if alvo.papel == PapelEnum.admin:
        raise HTTPException(
            status_code=409,
            detail="Não é possível remover um administrador por aqui.",
        )

    # Operador com movimentações registradas: bloqueia para preservar a trilha
    # de auditoria (movimentacoes.usuario_id é NOT NULL).
    tem_mov = db.query(Movimentacao).filter(Movimentacao.usuario_id == usuario_id).first()
    if tem_mov:
        raise HTTPException(
            status_code=409,
            detail="Operador possui movimentações registradas. Desative-o em vez de excluir.",
        )

    db.delete(alvo)
    db.commit()
