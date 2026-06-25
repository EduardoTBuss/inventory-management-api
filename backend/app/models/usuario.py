"""
Usuario model — usuários do sistema com acesso por papel.

Multi-tenant:
  - superadmin: sistema_id = NULL. Dono da plataforma; cria/gerencia sistemas.
                Faz login só com username + senha (sem código de sistema).
  - admin:      pertence a um sistema (sistema_id != NULL). Gerencia operadores,
                produtos, estoque e movimentações DAQUELE sistema. Tem e-mail.
  - operador:   pertence a um sistema. Registra movimentações. Login por
                username (nome de usuário) — não precisa de e-mail.

Login dentro de um sistema é identificado por (sistema_id, username).
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class PapelEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    operador = "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    # NULL apenas para superadmin; admin/operador sempre têm um sistema.
    sistema_id = Column(Integer, ForeignKey("sistemas.id"), nullable=True, index=True)
    nome = Column(String(120), nullable=False)
    # Identificador de login dentro do sistema. Único por (sistema_id, username).
    username = Column(String(60), nullable=False, index=True)
    # E-mail é opcional (operadores normalmente não têm).
    email = Column(String(180), nullable=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(Enum(PapelEnum), nullable=False, default=PapelEnum.operador)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    sistema = relationship("Sistema", back_populates="usuarios")

    __table_args__ = (
        UniqueConstraint("sistema_id", "username", name="uq_usuario_sistema_username"),
    )
