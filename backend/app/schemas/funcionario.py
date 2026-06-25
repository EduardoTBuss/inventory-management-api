"""
Schemas para a seção Funcionários/Equipe (acesso restrito a admin).

Cada FuncionarioStats agrega a atividade de um usuário:
  - total_vendido    : unidades em movimentações de tipo 'saida' que ele registrou
  - total_faturado   : SUM(quantidade * produto.preco_venda) dessas saídas
  - total_movimentacoes : nº de movimentações de qualquer tipo registradas por ele
  - ultima_atividade : data/hora da movimentação mais recente (None se nunca registrou)
"""

import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.models.usuario import PapelEnum


class FuncionarioStats(BaseModel):
    id: int
    nome: str
    username: str
    email: str | None = None
    papel: PapelEnum
    ativo: bool = True
    total_vendido: int
    total_faturado: float
    total_movimentacoes: int
    ultima_atividade: datetime | None = None


class EquipeOut(BaseModel):
    funcionarios: list[FuncionarioStats]
    total_funcionarios: int


class OperadorCreate(BaseModel):
    """Admin cria um operador no SEU sistema (sem precisar de e-mail)."""
    nome: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=2, max_length=60)
    senha: str = Field(min_length=4, max_length=128)

    @field_validator("username")
    @classmethod
    def _clean_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9._\-]+", v):
            raise ValueError("Usuário deve conter apenas letras, números, ponto, hífen ou _.")
        return v
