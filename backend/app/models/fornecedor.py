"""
Fornecedor model — product suppliers.

Multi-tenant: cada fornecedor pertence a um sistema.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True)
    sistema_id = Column(Integer, ForeignKey("sistemas.id"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    contato = Column(String(120), nullable=True)
    email = Column(String(180), nullable=True)
    telefone = Column(String(30), nullable=True)

    produtos = relationship("Produto", back_populates="fornecedor")
