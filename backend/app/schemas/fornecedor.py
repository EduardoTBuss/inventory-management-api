"""
Pydantic schemas for Fornecedor.
"""

from pydantic import BaseModel


class FornecedorBase(BaseModel):
    nome: str
    contato: str | None = None
    email: str | None = None
    telefone: str | None = None


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(BaseModel):
    nome: str | None = None
    contato: str | None = None
    email: str | None = None
    telefone: str | None = None


class FornecedorOut(FornecedorBase):
    id: int

    model_config = {"from_attributes": True}
