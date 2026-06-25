"""
Produto model.

CRITICAL INVARIANT: `quantidade` is NEVER updated directly via the API.
It is a projection of all movimentacoes. Every stock change must go through
movimentacao_service.registrar_movimentacao(), which updates both tables
inside the same transaction.

Multi-tenant: cada produto pertence a um sistema (sistema_id). O SKU é único
APENAS dentro do sistema — sistemas diferentes podem ter o mesmo SKU.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    sistema_id = Column(Integer, ForeignKey("sistemas.id"), nullable=False, index=True)
    nome = Column(String(150), nullable=False)
    sku = Column(String(80), nullable=False, index=True)
    preco_custo = Column(Float, nullable=False, default=0.0)
    preco_venda = Column(Float, nullable=False, default=0.0)
    quantidade = Column(Integer, nullable=False, default=0)
    qtd_minima = Column(Integer, nullable=False, default=5)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=True)
    imagem_url = Column(String(500), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    categoria = relationship("Categoria", back_populates="produtos")
    fornecedor = relationship("Fornecedor", back_populates="produtos")
    movimentacoes = relationship("Movimentacao", back_populates="produto")

    __table_args__ = (
        UniqueConstraint("sistema_id", "sku", name="uq_produto_sistema_sku"),
    )
