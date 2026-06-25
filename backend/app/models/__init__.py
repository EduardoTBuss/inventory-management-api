"""
Import all models so Alembic's autogenerate can discover them via Base.metadata.
"""

from app.models.sistema import Sistema  # noqa: F401
from app.models.usuario import Usuario, PapelEnum  # noqa: F401
from app.models.categoria import Categoria  # noqa: F401
from app.models.fornecedor import Fornecedor  # noqa: F401
from app.models.produto import Produto  # noqa: F401
from app.models.movimentacao import Movimentacao, TipoMovimentacaoEnum  # noqa: F401
