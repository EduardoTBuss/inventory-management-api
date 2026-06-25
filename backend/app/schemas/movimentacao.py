"""
Pydantic schemas for Movimentacao.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.movimentacao import TipoMovimentacaoEnum


class MovimentacaoCreate(BaseModel):
    produto_id: int
    tipo: TipoMovimentacaoEnum
    quantidade: int = Field(gt=0, description="Must be a positive integer")
    motivo: str | None = None


class MovimentacaoOut(BaseModel):
    id: int
    produto_id: int
    produto_nome: str | None = None
    tipo: TipoMovimentacaoEnum
    quantidade: int
    motivo: str | None = None
    usuario_id: int
    usuario_nome: str | None = None
    criado_em: datetime

    model_config = {"from_attributes": True}


class MovimentacaoPaginada(BaseModel):
    items: list[MovimentacaoOut]
    total: int
    page: int
    pages: int
