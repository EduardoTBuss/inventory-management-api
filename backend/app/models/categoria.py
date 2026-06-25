"""
Categoria model — product categories.

Multi-tenant: cada categoria pertence a um sistema. O nome é único apenas
dentro do sistema.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    sistema_id = Column(Integer, ForeignKey("sistemas.id"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255), nullable=True)

    produtos = relationship("Produto", back_populates="categoria")

    __table_args__ = (
        UniqueConstraint("sistema_id", "nome", name="uq_categoria_sistema_nome"),
    )
