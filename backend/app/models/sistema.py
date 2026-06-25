"""
Sistema model — a tenant. Cada Sistema é um "estoque" isolado, com seu próprio
admin, operadores, produtos, categorias, fornecedores e movimentações.

O servidor (PC do dono) hospeda VÁRIOS sistemas em paralelo no mesmo processo;
o isolamento é lógico, via a coluna sistema_id presente em todas as tabelas de
domínio. Um admin/operador do sistema A nunca enxerga dados do sistema B.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Sistema(Base):
    __tablename__ = "sistemas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    # `codigo` é o identificador curto usado no login (ex.: "loja-maria").
    codigo = Column(String(60), unique=True, nullable=False, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuarios = relationship("Usuario", back_populates="sistema")
