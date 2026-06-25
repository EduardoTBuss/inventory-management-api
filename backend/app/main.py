"""
FastAPI application entry point.

Startup sequence:
  1. Create all DB tables (dev convenience; Alembic handles prod migrations).
  2. Register routers under /api prefix.
  3. Mount frontend static files at / (served after API routes are matched first).
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.database import engine, Base

# Import all models so SQLAlchemy knows about them before create_all
import app.models  # noqa: F401 — side-effect import registers all ORM classes

from app.routes.auth import router as auth_router
from app.routes.sistemas import router as sistemas_router
from app.routes.produtos import router as produtos_router
from app.routes.categorias import router as categorias_router
from app.routes.fornecedores import router as fornecedores_router
from app.routes.movimentacoes import router as movimentacoes_router
from app.routes.dashboard import router as dashboard_router
from app.routes.funcionarios import router as funcionarios_router

# ── Create tables on startup (dev) ───────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gestão de Estoque",
    version="2.0.0",
    description="Inventory management system (multi-tenant) with event-sourcing-lite stock control.",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(sistemas_router, prefix="/api/sistemas", tags=["sistemas"])
app.include_router(produtos_router, prefix="/api/produtos", tags=["produtos"])
app.include_router(categorias_router, prefix="/api/categorias", tags=["categorias"])
app.include_router(fornecedores_router, prefix="/api/fornecedores", tags=["fornecedores"])
app.include_router(movimentacoes_router, prefix="/api/movimentacoes", tags=["movimentacoes"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(funcionarios_router, prefix="/api/funcionarios", tags=["funcionarios"])


# ── Frontend static files ─────────────────────────────────────────────────────
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(os.path.dirname(_BACKEND_DIR), "frontend")


class NoCacheStaticFiles(StaticFiles):
    """
    StaticFiles que força o navegador a sempre revalidar HTML/CSS/JS.
    `no-cache` não impede o cache — apenas obriga a checar com o servidor
    (via ETag) antes de reusar, então atualizações aparecem na hora.
    """

    async def get_response(self, path, scope):
        response: Response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", NoCacheStaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Gestão de Estoque API — frontend not found"}
