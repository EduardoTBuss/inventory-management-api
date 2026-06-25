"""
Pydantic schemas para Usuario e login multi-tenant.
"""

from datetime import datetime
from pydantic import BaseModel
from app.models.usuario import PapelEnum


class UsuarioOut(BaseModel):
    id: int
    nome: str
    username: str
    email: str | None = None
    papel: PapelEnum
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class UsuarioPublico(BaseModel):
    """Info mínima retornada no login e em respostas aninhadas."""
    id: int
    nome: str
    username: str
    email: str | None = None
    papel: PapelEnum
    sistema_id: int | None = None
    sistema_nome: str | None = None
    sistema_codigo: str | None = None

    model_config = {"from_attributes": True}


class LoginInput(BaseModel):
    """
    Login multi-tenant:
      - admin/operador: informam `codigo` (do sistema) + `usuario` + `senha`.
      - superadmin: deixa `codigo` vazio/None e informa `usuario` + `senha`.
    """
    codigo: str | None = None
    usuario: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublico
