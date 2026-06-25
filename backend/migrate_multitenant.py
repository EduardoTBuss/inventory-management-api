"""
Migração para multi-tenant.

Transforma o banco antigo (single-tenant) no novo schema multi-sistema:
  - cria a tabela `sistemas` e o "Sistema Principal" (código `principal`);
  - move TODOS os dados existentes (categorias, fornecedores, produtos,
    movimentações, usuários) para o Sistema Principal (sistema_id = 1),
    preservando os IDs e as relações;
  - gera `username` para os usuários antigos a partir do e-mail;
  - cria o super-admin da plataforma (sistema_id NULL).

Segurança:
  - Faz BACKUP do estoque.db antes de qualquer coisa.
  - É IDEMPOTENTE: se já houver tabela `sistemas`, não faz nada.

Uso (a partir de backend/):
    python migrate_multitenant.py

Credenciais geradas:
  - super-admin: usuario `superadmin`, senha = env SUPERADMIN_SENHA ou "super123".
  - admins/operadores antigos: username derivado do e-mail (ex.: admin@estoque.com -> "admin").
    A senha deles continua a MESMA de antes.
"""

import os
import sys
import shutil
import sqlite3
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import BASE_DIR, engine, SessionLocal, Base  # noqa: E402
import app.models  # noqa: F401,E402  (registra os models)
from app.models.sistema import Sistema  # noqa: E402
from app.models.usuario import Usuario, PapelEnum  # noqa: E402
from app.models.categoria import Categoria  # noqa: E402
from app.models.fornecedor import Fornecedor  # noqa: E402
from app.models.produto import Produto  # noqa: E402
from app.models.movimentacao import Movimentacao, TipoMovimentacaoEnum  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402

DB_PATH = os.path.join(BASE_DIR, "estoque.db")
SISTEMA_PRINCIPAL_ID = 1
SUPERADMIN_SENHA = os.environ.get("SUPERADMIN_SENHA", "super123")


def _read_old_data(path: str) -> dict:
    """Lê todas as linhas das tabelas antigas como lista de dicts."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    out = {}
    for tabela in ["usuarios", "categorias", "fornecedores", "produtos", "movimentacoes"]:
        try:
            rows = conn.execute(f"SELECT * FROM {tabela}").fetchall()
            out[tabela] = [dict(r) for r in rows]
        except sqlite3.OperationalError:
            out[tabela] = []
    out["_tabelas"] = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()
    return out


def _slug_username(email: str | None, nome: str, usados: set) -> str:
    base = ""
    if email and "@" in email:
        base = email.split("@", 1)[0]
    if not base:
        base = nome or "usuario"
    base = re.sub(r"[^a-z0-9._\-]", "", base.strip().lower()) or "usuario"
    username = base
    i = 1
    while username in usados:
        i += 1
        username = f"{base}{i}"
    usados.add(username)
    return username


def main():
    if not os.path.exists(DB_PATH):
        print("Nenhum estoque.db encontrado — criando schema novo + super-admin do zero.")
        Base.metadata.create_all(bind=engine)
        _criar_superadmin_se_preciso()
        return

    # Idempotência: já migrado?
    old = _read_old_data(DB_PATH)
    if "sistemas" in old["_tabelas"]:
        print("[=] Tabela 'sistemas' já existe — banco já parece migrado. Nada a fazer.")
        return

    # 1) Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BASE_DIR, f"estoque_backup_pre_multitenant_{ts}.db")
    shutil.copy2(DB_PATH, backup_path)
    print(f"[+] Backup criado: {os.path.basename(backup_path)}")

    # 2) Recria o banco com o schema novo
    engine.dispose()
    os.remove(DB_PATH)
    Base.metadata.create_all(bind=engine)
    print("[+] Schema novo criado.")

    db = SessionLocal()
    try:
        # 3) Sistema Principal (id=1)
        sistema = Sistema(id=SISTEMA_PRINCIPAL_ID, nome="Sistema Principal", codigo="principal")
        db.add(sistema)
        db.flush()
        print("[+] Sistema Principal (código 'principal') criado.")

        # 4) Usuários antigos -> sistema 1, com username derivado do e-mail
        usados: set = set()
        for u in old["usuarios"]:
            papel_raw = (u.get("papel") or "operador")
            papel = PapelEnum.admin if papel_raw == "admin" else PapelEnum.operador
            username = _slug_username(u.get("email"), u.get("nome", ""), usados)
            db.add(Usuario(
                id=u["id"],
                sistema_id=SISTEMA_PRINCIPAL_ID,
                nome=u.get("nome") or username,
                username=username,
                email=u.get("email"),
                senha_hash=u["senha_hash"],
                papel=papel,
                ativo=True,
                criado_em=_parse_dt(u.get("criado_em")),
            ))
            print(f"    usuario #{u['id']}: {u.get('email')} -> login '{username}' ({papel.value})")

        # 5) Categorias
        for c in old["categorias"]:
            db.add(Categoria(
                id=c["id"], sistema_id=SISTEMA_PRINCIPAL_ID,
                nome=c["nome"], descricao=c.get("descricao"),
            ))

        # 6) Fornecedores
        for f in old["fornecedores"]:
            db.add(Fornecedor(
                id=f["id"], sistema_id=SISTEMA_PRINCIPAL_ID,
                nome=f["nome"], contato=f.get("contato"),
                email=f.get("email"), telefone=f.get("telefone"),
            ))

        # 7) Produtos
        for p in old["produtos"]:
            db.add(Produto(
                id=p["id"], sistema_id=SISTEMA_PRINCIPAL_ID,
                nome=p["nome"], sku=p["sku"],
                preco_custo=p.get("preco_custo") or 0.0,
                preco_venda=p.get("preco_venda") or 0.0,
                quantidade=p.get("quantidade") or 0,
                qtd_minima=p.get("qtd_minima") or 0,
                categoria_id=p["categoria_id"],
                fornecedor_id=p.get("fornecedor_id"),
                imagem_url=p.get("imagem_url"),
                criado_em=_parse_dt(p.get("criado_em")),
                atualizado_em=_parse_dt(p.get("atualizado_em")),
            ))

        # 8) Movimentações
        for m in old["movimentacoes"]:
            db.add(Movimentacao(
                id=m["id"], sistema_id=SISTEMA_PRINCIPAL_ID,
                produto_id=m["produto_id"],
                tipo=TipoMovimentacaoEnum(m["tipo"]),
                quantidade=m["quantidade"],
                motivo=m.get("motivo"),
                usuario_id=m["usuario_id"],
                criado_em=_parse_dt(m.get("criado_em")),
            ))

        db.commit()
        print(f"[+] Migrados: {len(old['usuarios'])} usuários, {len(old['categorias'])} categorias, "
              f"{len(old['fornecedores'])} fornecedores, {len(old['produtos'])} produtos, "
              f"{len(old['movimentacoes'])} movimentações.")

        # 9) Super-admin
        _criar_superadmin_se_preciso(db)

        _verificar(db)
    finally:
        db.close()

    print("\n[OK] Migração concluída.")
    print(f"     Login do Sistema Principal: código 'principal' + usuário (ver acima) + senha antiga.")
    print(f"     Super-admin: usuário 'superadmin' + senha '{SUPERADMIN_SENHA}' (sem código).")


def _criar_superadmin_se_preciso(db=None):
    own = db is None
    if own:
        db = SessionLocal()
    try:
        existe = (
            db.query(Usuario)
            .filter(Usuario.sistema_id.is_(None), Usuario.papel == PapelEnum.superadmin)
            .first()
        )
        if existe:
            print(f"[=] Super-admin já existe (usuário '{existe.username}').")
            return
        db.add(Usuario(
            sistema_id=None,
            nome="Super Administrador",
            username="superadmin",
            email=None,
            senha_hash=hash_password(SUPERADMIN_SENHA),
            papel=PapelEnum.superadmin,
            ativo=True,
        ))
        db.commit()
        print(f"[+] Super-admin criado: usuário 'superadmin' / senha '{SUPERADMIN_SENHA}'.")
    finally:
        if own:
            db.close()


def _parse_dt(value):
    if value is None:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    s = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def _verificar(db):
    """Confere a invariante de estoque por produto após a migração."""
    erros = []
    for p in db.query(Produto).all():
        esperado = sum(
            m.quantidade if m.tipo in (TipoMovimentacaoEnum.entrada, TipoMovimentacaoEnum.ajuste)
            else -m.quantidade
            for m in p.movimentacoes
        )
        if p.quantidade != esperado:
            erros.append(f"  INVARIANTE FALHOU {p.sku}: quantidade={p.quantidade}, esperado={esperado}")
    if erros:
        print("\n".join(erros))
        print("[!] Aviso: invariante divergente (pode ser ajuste manual antigo). Backup preservado.")
    else:
        print(f"[OK] Invariante de estoque verificada em {db.query(Produto).count()} produtos.")


if __name__ == "__main__":
    main()
