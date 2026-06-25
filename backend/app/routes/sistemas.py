"""
Rotas de Sistemas (tenants) — ACESSO RESTRITO AO SUPER-ADMIN.

  GET    /api/sistemas        → lista todos os sistemas (com contagens)
  POST   /api/sistemas        → cria um sistema + seu primeiro admin
  DELETE /api/sistemas/{id}   → remove um sistema e TODOS os seus dados
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.sistema import Sistema
from app.models.usuario import Usuario, PapelEnum
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.movimentacao import Movimentacao
from app.schemas.sistema import SistemaCreate, SistemaOut
from app.services.auth_service import hash_password
from app.auth.dependencies import require_superadmin

router = APIRouter()


def _to_out(db: Session, sistema: Sistema) -> SistemaOut:
    total_usuarios = (
        db.query(func.count(Usuario.id)).filter(Usuario.sistema_id == sistema.id).scalar()
    )
    total_produtos = (
        db.query(func.count(Produto.id)).filter(Produto.sistema_id == sistema.id).scalar()
    )
    admin = (
        db.query(Usuario)
        .filter(Usuario.sistema_id == sistema.id, Usuario.papel == PapelEnum.admin)
        .order_by(Usuario.id)
        .first()
    )
    return SistemaOut(
        id=sistema.id,
        nome=sistema.nome,
        codigo=sistema.codigo,
        criado_em=sistema.criado_em,
        total_usuarios=int(total_usuarios or 0),
        total_produtos=int(total_produtos or 0),
        admin_nome=admin.nome if admin else None,
        admin_username=admin.username if admin else None,
    )


@router.get("", response_model=list[SistemaOut])
def listar_sistemas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
):
    sistemas = db.query(Sistema).order_by(Sistema.nome).all()
    return [_to_out(db, s) for s in sistemas]


@router.post("", response_model=SistemaOut, status_code=status.HTTP_201_CREATED)
def criar_sistema(
    dados: SistemaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
):
    if db.query(Sistema).filter(Sistema.codigo == dados.codigo).first():
        raise HTTPException(
            status_code=422, detail=f"Já existe um sistema com o código '{dados.codigo}'"
        )

    sistema = Sistema(nome=dados.nome.strip(), codigo=dados.codigo)
    db.add(sistema)
    db.flush()  # obtém sistema.id sem commitar

    admin = Usuario(
        sistema_id=sistema.id,
        nome=dados.admin_nome.strip(),
        username=dados.admin_username,
        email=(dados.admin_email or None),
        senha_hash=hash_password(dados.admin_senha),
        papel=PapelEnum.admin,
        ativo=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(sistema)
    return _to_out(db, sistema)


@router.delete("/{sistema_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_sistema(
    sistema_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_superadmin),
):
    sistema = db.query(Sistema).filter(Sistema.id == sistema_id).first()
    if not sistema:
        raise HTTPException(status_code=404, detail="Sistema não encontrado")

    # Remove todos os dados do tenant em ordem segura (respeitando dependências).
    db.query(Movimentacao).filter(Movimentacao.sistema_id == sistema_id).delete(synchronize_session=False)
    db.query(Produto).filter(Produto.sistema_id == sistema_id).delete(synchronize_session=False)
    db.query(Fornecedor).filter(Fornecedor.sistema_id == sistema_id).delete(synchronize_session=False)
    db.query(Categoria).filter(Categoria.sistema_id == sistema_id).delete(synchronize_session=False)
    db.query(Usuario).filter(Usuario.sistema_id == sistema_id).delete(synchronize_session=False)
    db.delete(sistema)
    db.commit()
