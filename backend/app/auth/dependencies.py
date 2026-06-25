"""
FastAPI dependency functions for authentication and authorization.

Camadas:
  - get_current_user   : decodifica o token e devolve o Usuario.
  - require_admin       : exige papel admin (admin de um sistema).
  - require_superadmin  : exige papel superadmin (dono da plataforma).
  - get_sistema_id      : devolve o sistema_id do usuário logado e BARRA o
                          superadmin (que não pertence a nenhum sistema) de
                          acessar endpoints de domínio (produtos, estoque, etc.).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt import decode_token
from app.models.usuario import Usuario, PapelEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Decode the Bearer token and return the corresponding Usuario.
    Raises 401 if token is invalid / user inactive, 401 if user no longer exists.
    """
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Exige papel 'admin' (admin de um sistema). Superadmin NÃO é admin de sistema.
    Raises 403 otherwise.
    """
    if current_user.papel != PapelEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores do sistema",
        )
    return current_user


def require_superadmin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Exige papel 'superadmin' (dono da plataforma). Raises 403 otherwise."""
    if current_user.papel != PapelEnum.superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao super-administrador da plataforma",
        )
    return current_user


def get_sistema_id(current_user: Usuario = Depends(get_current_user)) -> int:
    """
    Devolve o sistema_id do usuário logado. Usado para escopar TODOS os
    endpoints de domínio. Barra o superadmin (sistema_id None) — ele gerencia
    sistemas, não estoque.
    """
    if current_user.sistema_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta seção pertence a um sistema. Entre como admin ou operador de um sistema.",
        )
    return current_user.sistema_id
