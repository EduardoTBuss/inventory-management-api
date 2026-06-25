"""
Pydantic schemas para Sistema (tenant) — usados pelo painel do super-admin.
"""

import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SistemaCreate(BaseModel):
    """Cria um sistema novo JUNTO do seu primeiro admin."""
    nome: str = Field(min_length=2, max_length=120)
    codigo: str = Field(min_length=2, max_length=60)
    admin_nome: str = Field(min_length=2, max_length=120)
    admin_username: str = Field(min_length=2, max_length=60)
    admin_senha: str = Field(min_length=4, max_length=128)
    admin_email: str | None = None

    @field_validator("codigo")
    @classmethod
    def _slug_codigo(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", v):
            raise ValueError(
                "Código deve conter apenas letras minúsculas, números e hífens "
                "(ex.: loja-maria)."
            )
        return v

    @field_validator("admin_username")
    @classmethod
    def _clean_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9._\-]+", v):
            raise ValueError("Usuário deve conter apenas letras, números, ponto, hífen ou _.")
        return v


class SistemaOut(BaseModel):
    id: int
    nome: str
    codigo: str
    criado_em: datetime
    total_usuarios: int = 0
    total_produtos: int = 0
    admin_nome: str | None = None
    admin_username: str | None = None

    model_config = {"from_attributes": True}
