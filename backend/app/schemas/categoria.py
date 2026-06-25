"""
Pydantic schemas for Categoria.
"""

from pydantic import BaseModel


class CategoriaBase(BaseModel):
    nome: str
    descricao: str | None = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None


class CategoriaOut(CategoriaBase):
    id: int

    model_config = {"from_attributes": True}
