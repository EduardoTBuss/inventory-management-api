"""
Movimentacao model — immutable audit log of every stock change.

tipo:
  - "entrada"  → stock increases  (delta = +quantidade)
  - "saida"    → stock decreases  (delta = -quantidade)
  - "ajuste"   → manual correction (delta = +quantidade for positive adjustments;
                  use negative values handled at service level if needed — currently
                  ajuste always adds, use saida for decrements)

Multi-tenant: cada movimentação pertence a um sistema (sistema_id), redundante
com produto.sistema_id mas presente para escopar consultas sem JOIN.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class TipoMovimentacaoEnum(str, enum.Enum):
    entrada = "entrada"
    saida = "saida"
    ajuste = "ajuste"


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    sistema_id = Column(Integer, ForeignKey("sistemas.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)
    tipo = Column(Enum(TipoMovimentacaoEnum), nullable=False)
    quantidade = Column(Integer, nullable=False)  # always positive; sign derived from tipo
    motivo = Column(String(300), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    produto = relationship("Produto", back_populates="movimentacoes")
    usuario = relationship("Usuario")
