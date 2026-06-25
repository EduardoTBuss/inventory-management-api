"""
Auth routes:
  POST /api/auth/login  → issue JWT (multi-tenant)
  GET  /api/auth/me     → current user info

Login multi-tenant:
  - admin/operador: { codigo, usuario, senha } → resolve sistema pelo `codigo`,
    depois o usuário por (sistema_id, username).
  - superadmin: { usuario, senha } (codigo vazio) → usuário com sistema_id NULL.
"""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario, PapelEnum
from app.models.sistema import Sistema
from app.schemas.usuario import LoginInput, TokenResponse, UsuarioPublico
from app.services.auth_service import verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter()

# Rate limit de login em memória: bloqueia força-bruta básica sem dependência
# externa. Por processo único (uvicorn dev) é suficiente; com múltiplos workers
# ou réplicas, mover para Redis/proxy reverso.
_LOGIN_MAX_FAILURES = 5
_LOGIN_WINDOW_SECONDS = 60
_login_failures: dict[str, deque] = defaultdict(deque)


def _is_rate_limited(ip: str) -> bool:
    now = time.monotonic()
    failures = _login_failures[ip]
    while failures and now - failures[0] > _LOGIN_WINDOW_SECONDS:
        failures.popleft()
    return len(failures) >= _LOGIN_MAX_FAILURES


def _register_failure(ip: str) -> None:
    _login_failures[ip].append(time.monotonic())


def _publico(user: Usuario) -> UsuarioPublico:
    return UsuarioPublico(
        id=user.id,
        nome=user.nome,
        username=user.username,
        email=user.email,
        papel=user.papel,
        sistema_id=user.sistema_id,
        sistema_nome=user.sistema.nome if user.sistema else None,
        sistema_codigo=user.sistema.codigo if user.sistema else None,
    )


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginInput, request: Request, db: Session = Depends(get_db)):
    """
    Autentica com (codigo opcional) + usuario + senha. Mensagem de erro vaga
    de propósito para evitar enumeração de usuários/sistemas.
    """
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Aguarde um minuto e tente novamente.",
            headers={"Retry-After": str(_LOGIN_WINDOW_SECONDS)},
        )

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Código, usuário ou senha inválidos",
    )

    username = (dados.usuario or "").strip().lower()
    codigo = (dados.codigo or "").strip().lower()

    if codigo:
        # Login dentro de um sistema (admin/operador).
        sistema = db.query(Sistema).filter(Sistema.codigo == codigo).first()
        if not sistema:
            _register_failure(client_ip)
            raise invalid
        user = (
            db.query(Usuario)
            .filter(Usuario.sistema_id == sistema.id, Usuario.username == username)
            .first()
        )
    else:
        # Sem código → superadmin (sistema_id NULL).
        user = (
            db.query(Usuario)
            .filter(
                Usuario.sistema_id.is_(None),
                Usuario.username == username,
                Usuario.papel == PapelEnum.superadmin,
            )
            .first()
        )

    if not user or not user.ativo or not verify_password(dados.senha, user.senha_hash):
        _register_failure(client_ip)
        raise invalid

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=_publico(user),
    )


@router.get("/me", response_model=UsuarioPublico)
def me(current_user: Usuario = Depends(get_current_user)):
    """Return the authenticated user's public profile."""
    return _publico(current_user)
