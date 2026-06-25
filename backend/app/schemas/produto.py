"""
Pydantic schemas for Produto.

NOTE: `quantidade` is intentionally excluded from ProdutoCreate and ProdutoUpdate.
Stock is always managed through movimentacoes.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ProdutoBase(BaseModel):
    nome: str
    sku: str
    preco_custo: float = Field(ge=0)
    preco_venda: float = Field(ge=0)
    qtd_minima: int = Field(ge=0, default=5)
    categoria_id: int
    fornecedor_id: int | None = None
    imagem_url: str | None = None


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    """
    All fields optional for partial updates.
    `quantidade` is explicitly absent — use movimentacoes.
    """
    nome: str | None = None
    sku: str | None = None
    preco_custo: float | None = Field(default=None, ge=0)
    preco_venda: float | None = Field(default=None, ge=0)
    qtd_minima: int | None = Field(default=None, ge=0)
    categoria_id: int | None = None
    fornecedor_id: int | None = None
    imagem_url: str | None = None


class ProdutoOut(BaseModel):
    id: int
    nome: str
    sku: str
    preco_custo: float
    preco_venda: float
    quantidade: int
    qtd_minima: int
    categoria_id: int
    categoria_nome: str | None = None
    fornecedor_id: int | None = None
    fornecedor_nome: str | None = None
    imagem_url: str | None = None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class ProdutoPaginado(BaseModel):
    items: list[ProdutoOut]
    total: int
    page: int
    pages: int


class ProdutoResumo(BaseModel):
    """Compact representation used in dashboard responses."""
    id: int
    nome: str
    sku: str
    quantidade: int
    qtd_minima: int

    model_config = {"from_attributes": True}
