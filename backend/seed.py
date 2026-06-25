"""
Seed script — popula o banco com dados de demonstração (multi-tenant).

Cria:
  - super-admin da plataforma (usuario 'superadmin' / senha 'super123', sem sistema)
  - Sistema "Sistema Principal" (codigo 'principal')
  - admin do principal (usuario 'admin' / senha 'admin123')
  - operador do principal (usuario 'op' / senha 'op123')
  - categorias, fornecedores, produtos e ~50 movimentações — todos no principal.

Rodar a partir de backend/:
    python seed.py

Idempotente: pula registros que já existem.

INVARIANTE auditada no fim: produto.quantidade == SUM(delta das movimentacoes).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import engine, SessionLocal, Base
from app.models import Sistema, Usuario, Categoria, Fornecedor, Produto, Movimentacao
from app.models.usuario import PapelEnum
from app.models.movimentacao import TipoMovimentacaoEnum
from app.services.auth_service import hash_password

Base.metadata.create_all(bind=engine)

CODIGO_PRINCIPAL = "principal"


def seed():
    db = SessionLocal()
    try:
        sistema = _seed_sistema(db)
        _seed_superadmin(db)
        _seed_usuarios(db, sistema)
        _seed_categorias(db, sistema)
        _seed_fornecedores(db, sistema)
        _seed_produtos(db, sistema)
        _seed_movimentacoes(db, sistema)
        _verify_invariant(db)
        print("\nSeed completed successfully.")
    finally:
        db.close()


# ── Sistema ───────────────────────────────────────────────────────────────────

def _seed_sistema(db) -> Sistema:
    sistema = db.query(Sistema).filter(Sistema.codigo == CODIGO_PRINCIPAL).first()
    if not sistema:
        sistema = Sistema(nome="Sistema Principal", codigo=CODIGO_PRINCIPAL)
        db.add(sistema)
        db.commit()
        db.refresh(sistema)
        print(f"  [+] sistema: {sistema.nome} (codigo '{sistema.codigo}')")
    return sistema


# ── Super-admin ───────────────────────────────────────────────────────────────

def _seed_superadmin(db):
    existe = (
        db.query(Usuario)
        .filter(Usuario.sistema_id.is_(None), Usuario.papel == PapelEnum.superadmin)
        .first()
    )
    if not existe:
        db.add(Usuario(
            sistema_id=None,
            nome="Super Administrador",
            username="superadmin",
            email=None,
            senha_hash=hash_password("super123"),
            papel=PapelEnum.superadmin,
            ativo=True,
        ))
        db.commit()
        print("  [+] super-admin: superadmin / super123")


# ── Usuarios do sistema principal ─────────────────────────────────────────────

def _seed_usuarios(db, sistema: Sistema):
    users = [
        {"nome": "Administrador", "username": "admin", "email": "admin@estoque.com", "senha": "admin123", "papel": PapelEnum.admin},
        {"nome": "Operador Padrão", "username": "op", "email": "op@estoque.com", "senha": "op123", "papel": PapelEnum.operador},
    ]
    for u in users:
        existe = (
            db.query(Usuario)
            .filter(Usuario.sistema_id == sistema.id, Usuario.username == u["username"])
            .first()
        )
        if not existe:
            db.add(Usuario(
                sistema_id=sistema.id,
                nome=u["nome"],
                username=u["username"],
                email=u["email"],
                senha_hash=hash_password(u["senha"]),
                papel=u["papel"],
                ativo=True,
            ))
            print(f"  [+] usuario: {u['username']} ({u['papel'].value})")
    db.commit()


# ── Categorias ────────────────────────────────────────────────────────────────

CATEGORIAS = [
    {"nome": "Eletrônicos", "descricao": "Dispositivos eletrônicos e acessórios"},
    {"nome": "Alimentos", "descricao": "Produtos alimentícios e bebidas"},
    {"nome": "Vestuário", "descricao": "Roupas, calçados e acessórios de moda"},
    {"nome": "Ferramentas", "descricao": "Ferramentas manuais e elétricas"},
    {"nome": "Limpeza", "descricao": "Produtos de limpeza e higiene"},
]


def _seed_categorias(db, sistema: Sistema):
    for c in CATEGORIAS:
        existe = (
            db.query(Categoria)
            .filter(Categoria.sistema_id == sistema.id, Categoria.nome == c["nome"])
            .first()
        )
        if not existe:
            db.add(Categoria(sistema_id=sistema.id, **c))
            print(f"  [+] categoria: {c['nome']}")
    db.commit()


# ── Fornecedores ──────────────────────────────────────────────────────────────

FORNECEDORES = [
    {"nome": "TechSupply Ltda", "contato": "Carlos Mendes", "email": "carlos@techsupply.com.br", "telefone": "(11) 9 8765-4321"},
    {"nome": "Distribuidora Brasil", "contato": "Ana Lima", "email": "ana@distbrasil.com.br", "telefone": "(21) 9 9123-5678"},
    {"nome": "Global Parts S.A.", "contato": "Roberto Souza", "email": "roberto@globalparts.com", "telefone": "(31) 9 7654-3210"},
]


def _seed_fornecedores(db, sistema: Sistema):
    for f in FORNECEDORES:
        existe = (
            db.query(Fornecedor)
            .filter(Fornecedor.sistema_id == sistema.id, Fornecedor.nome == f["nome"])
            .first()
        )
        if not existe:
            db.add(Fornecedor(sistema_id=sistema.id, **f))
            print(f"  [+] fornecedor: {f['nome']}")
    db.commit()


# ── Produtos ──────────────────────────────────────────────────────────────────

def _seed_produtos(db, sistema: Sistema):
    cat = {c.nome: c.id for c in db.query(Categoria).filter(Categoria.sistema_id == sistema.id).all()}
    forn = {f.nome: f.id for f in db.query(Fornecedor).filter(Fornecedor.sistema_id == sistema.id).all()}

    produtos_data = [
        {"nome": "Smartphone Samsung Galaxy A54", "sku": "ELE-001", "preco_custo": 950.00, "preco_venda": 1349.90, "qtd_minima": 3, "categoria_id": cat["Eletrônicos"], "fornecedor_id": forn["TechSupply Ltda"]},
        {"nome": "Notebook Dell Inspiron 15", "sku": "ELE-002", "preco_custo": 2800.00, "preco_venda": 3699.90, "qtd_minima": 2, "categoria_id": cat["Eletrônicos"], "fornecedor_id": forn["TechSupply Ltda"]},
        {"nome": "Fone de Ouvido Bluetooth JBL", "sku": "ELE-003", "preco_custo": 180.00, "preco_venda": 299.90, "qtd_minima": 5, "categoria_id": cat["Eletrônicos"], "fornecedor_id": forn["TechSupply Ltda"]},
        {"nome": "Carregador USB-C 65W", "sku": "ELE-004", "preco_custo": 45.00, "preco_venda": 89.90, "qtd_minima": 10, "categoria_id": cat["Eletrônicos"], "fornecedor_id": forn["Global Parts S.A."]},
        {"nome": "Café Especial Grão Fino 500g", "sku": "ALI-001", "preco_custo": 22.00, "preco_venda": 39.90, "qtd_minima": 20, "categoria_id": cat["Alimentos"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Azeite Extra Virgem 500ml", "sku": "ALI-002", "preco_custo": 18.00, "preco_venda": 32.90, "qtd_minima": 15, "categoria_id": cat["Alimentos"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Chocolate Amargo 70% 200g", "sku": "ALI-003", "preco_custo": 8.50, "preco_venda": 14.90, "qtd_minima": 25, "categoria_id": cat["Alimentos"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Camiseta Premium Algodão M", "sku": "VES-001", "preco_custo": 28.00, "preco_venda": 59.90, "qtd_minima": 10, "categoria_id": cat["Vestuário"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Calça Jeans Slim 42", "sku": "VES-002", "preco_custo": 65.00, "preco_venda": 129.90, "qtd_minima": 8, "categoria_id": cat["Vestuário"], "fornecedor_id": None},
        {"nome": "Tênis Casual Nike 40", "sku": "VES-003", "preco_custo": 180.00, "preco_venda": 349.90, "qtd_minima": 5, "categoria_id": cat["Vestuário"], "fornecedor_id": forn["Global Parts S.A."]},
        {"nome": "Furadeira de Impacto 750W", "sku": "FER-001", "preco_custo": 210.00, "preco_venda": 379.90, "qtd_minima": 3, "categoria_id": cat["Ferramentas"], "fornecedor_id": forn["Global Parts S.A."]},
        {"nome": "Chave de Fenda Phillips Kit 6pc", "sku": "FER-002", "preco_custo": 22.00, "preco_venda": 44.90, "qtd_minima": 10, "categoria_id": cat["Ferramentas"], "fornecedor_id": forn["Global Parts S.A."]},
        {"nome": "Desinfetante Pinho 2L", "sku": "LIM-001", "preco_custo": 8.00, "preco_venda": 15.90, "qtd_minima": 20, "categoria_id": cat["Limpeza"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Detergente Neutro 500ml", "sku": "LIM-002", "preco_custo": 3.50, "preco_venda": 6.90, "qtd_minima": 30, "categoria_id": cat["Limpeza"], "fornecedor_id": forn["Distribuidora Brasil"]},
        {"nome": "Álcool Gel 70% 500ml", "sku": "LIM-003", "preco_custo": 9.00, "preco_venda": 18.90, "qtd_minima": 15, "categoria_id": cat["Limpeza"], "fornecedor_id": forn["Distribuidora Brasil"]},
    ]

    for p in produtos_data:
        existe = (
            db.query(Produto)
            .filter(Produto.sistema_id == sistema.id, Produto.sku == p["sku"])
            .first()
        )
        if not existe:
            db.add(Produto(sistema_id=sistema.id, **p))
            print(f"  [+] produto: {p['nome']} ({p['sku']})")
    db.commit()


# ── Movimentações ─────────────────────────────────────────────────────────────

def _seed_movimentacoes(db, sistema: Sistema):
    admin = db.query(Usuario).filter(Usuario.sistema_id == sistema.id, Usuario.username == "admin").first()
    op = db.query(Usuario).filter(Usuario.sistema_id == sistema.id, Usuario.username == "op").first()
    produtos = {p.sku: p for p in db.query(Produto).filter(Produto.sistema_id == sistema.id).all()}

    if db.query(Movimentacao).filter(Movimentacao.sistema_id == sistema.id).count() > 0:
        print("  [=] movimentacoes already seeded, skipping")
        return

    def mov(sku, tipo, qtd, motivo, usuario, days_ago=0):
        p = produtos[sku]
        delta = -qtd if tipo == TipoMovimentacaoEnum.saida else qtd
        p.quantidade += delta
        p.atualizado_em = datetime.utcnow()
        db.add(Movimentacao(
            sistema_id=sistema.id,
            produto_id=p.id,
            tipo=tipo,
            quantidade=qtd,
            motivo=motivo,
            usuario_id=usuario.id,
            criado_em=datetime.utcnow() - timedelta(days=days_ago),
        ))

    E, S, A = TipoMovimentacaoEnum.entrada, TipoMovimentacaoEnum.saida, TipoMovimentacaoEnum.ajuste

    mov("ELE-001", E, 20, "Compra inicial do fornecedor", admin, 60)
    mov("ELE-001", S, 5,  "Venda para cliente corporativo", op, 55)
    mov("ELE-001", S, 3,  "Venda balcão", op, 40)
    mov("ELE-001", E, 10, "Reposição de estoque", admin, 20)
    mov("ELE-001", S, 4,  "Venda online", op, 5)
    mov("ELE-002", E, 8,  "Compra inicial", admin, 58)
    mov("ELE-002", S, 2,  "Venda para empresa", op, 50)
    mov("ELE-002", S, 1,  "Venda balcão", op, 30)
    mov("ELE-003", E, 30, "Compra em lote", admin, 45)
    mov("ELE-003", S, 8,  "Venda varejo", op, 40)
    mov("ELE-003", S, 5,  "Promoção relâmpago", op, 15)
    mov("ELE-003", E, 15, "Reposição", admin, 10)
    mov("ELE-004", E, 50, "Lote inicial", admin, 50)
    mov("ELE-004", S, 12, "Venda avulsa", op, 45)
    mov("ELE-004", S, 8,  "Venda kit smartphone", op, 20)
    mov("ALI-001", E, 100, "Compra quinzenal", admin, 30)
    mov("ALI-001", S, 25,  "Venda semana 1", op, 25)
    mov("ALI-001", S, 30,  "Venda semana 2", op, 18)
    mov("ALI-001", E, 80,  "Reposição mensal", admin, 10)
    mov("ALI-002", E, 60, "Compra mensal", admin, 28)
    mov("ALI-002", S, 15, "Venda regular", op, 20)
    mov("ALI-002", S, 20, "Promoção", op, 7)
    mov("ALI-003", E, 120, "Compra em lote", admin, 35)
    mov("ALI-003", S, 40,  "Vendas do mês", op, 20)
    mov("ALI-003", S, 30,  "Vendas da semana", op, 5)
    mov("VES-001", E, 50, "Coleção verão", admin, 90)
    mov("VES-001", S, 12, "Vendas semana 1", op, 85)
    mov("VES-001", S, 8,  "Vendas semana 2", op, 78)
    mov("VES-001", A, 2,  "Ajuste por contagem de inventário", admin, 60)
    mov("VES-002", E, 30, "Coleção inverno", admin, 80)
    mov("VES-002", S, 7,  "Vendas balcão", op, 70)
    mov("VES-002", S, 5,  "Vendas online", op, 40)
    mov("VES-003", E, 20, "Coleção nova", admin, 50)
    mov("VES-003", S, 6,  "Vendas", op, 30)
    mov("FER-001", E, 15, "Compra inicial", admin, 45)
    mov("FER-001", S, 4,  "Vendas pessoa física", op, 30)
    mov("FER-001", S, 3,  "Vendas pessoa jurídica", op, 10)
    mov("FER-002", E, 40, "Compra em lote", admin, 40)
    mov("FER-002", S, 10, "Vendas", op, 20)
    mov("LIM-001", E, 80, "Compra quinzenal", admin, 20)
    mov("LIM-001", S, 25, "Vendas semana 1", op, 15)
    mov("LIM-001", S, 15, "Vendas semana 2", op, 5)
    mov("LIM-002", E, 100, "Compra mensal", admin, 18)
    mov("LIM-002", S, 30,  "Vendas", op, 10)
    mov("LIM-003", E, 60, "Reposição", admin, 12)
    mov("LIM-003", S, 20, "Vendas", op, 6)

    db.commit()
    print(f"  [+] {db.query(Movimentacao).filter(Movimentacao.sistema_id == sistema.id).count()} movimentacoes created")


# ── Invariant check ───────────────────────────────────────────────────────────

def _verify_invariant(db):
    produtos = db.query(Produto).all()
    errors = []
    for p in produtos:
        expected = sum(
            m.quantidade if m.tipo in (TipoMovimentacaoEnum.entrada, TipoMovimentacaoEnum.ajuste)
            else -m.quantidade
            for m in p.movimentacoes
        )
        if p.quantidade != expected:
            errors.append(f"  INVARIANT FAIL {p.sku}: quantidade={p.quantidade}, expected={expected}")
    if errors:
        for e in errors:
            print(e)
        raise AssertionError("Audit invariant violated — see above")
    print(f"\n  [OK] Audit invariant verified for {len(produtos)} products")


if __name__ == "__main__":
    seed()
