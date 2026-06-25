# Multi-Sistemas (multi-tenant) — Guia

A partir da v2.0 o servidor (seu PC) hospeda **vários sistemas isolados em paralelo**.
Cada sistema é um estoque independente, com seu próprio admin, operadores, produtos,
categorias, fornecedores e movimentações. Um sistema **nunca** enxerga os dados de outro.

## Papéis

| Papel | Pertence a um sistema? | O que faz |
|---|---|---|
| **super-admin** | Não (dono da plataforma) | Cria, lista e exclui sistemas. Não acessa estoque. |
| **admin** | Sim | Gerencia produtos, estoque, categorias, fornecedores e **operadores** do seu sistema. |
| **operador** | Sim | Registra movimentações (entrada/saída/ajuste) e consulta o estoque do seu sistema. |

## Como entrar (login)

A tela de login tem três campos: **código do sistema**, **usuário** e **senha**.

- **Admin / operador:** informam o `código` do sistema + usuário + senha.
- **Super-admin:** deixa o **código em branco** e informa usuário + senha.

### Credenciais após a migração

| Quem | Código | Usuário | Senha |
|---|---|---|---|
| Super-admin | *(vazio)* | `superadmin` | `super123` |
| Admin do Sistema Principal | `principal` | `admin` | `admin123` |
| Operador do Sistema Principal | `principal` | `op` | `op123` |

> Troque a senha do super-admin assim que possível (veja "Variáveis" abaixo).
> Os usuários antigos foram preservados — a **senha deles continua a mesma**; só o
> login agora é por *usuário* (derivado do e-mail) em vez de e-mail.

## Fluxo de uso

1. **Super-admin** entra (sem código) → cai na tela **Sistemas**.
2. Clica em **Novo sistema**: informa nome, código (ex.: `loja-maria`) e os dados do
   **primeiro admin** daquele sistema (nome, usuário, senha; e-mail opcional).
3. O **admin** criado entra com o código do sistema + seu usuário + senha → cai no
   **Dashboard** do seu estoque.
4. Na aba **Equipe**, o admin cria **operadores** (nome + usuário + senha) do sistema.
5. **Operadores** entram com o código do sistema + usuário + senha e registram
   movimentações.

## Migração do banco existente

O banco antigo (single-tenant) é convertido para o "Sistema Principal" (código
`principal`) preservando todos os dados e IDs.

```bash
cd backend
python migrate_multitenant.py
```

- Faz **backup automático** do `estoque.db` antes de qualquer coisa
  (`estoque_backup_original_pre_multitenant.db`).
- É **idempotente**: se já houver a tabela `sistemas`, não faz nada.
- Cria o super-admin e verifica a invariante de estoque ao final.

Para instalações **do zero** (sem banco), use o seed (cria tudo, inclusive o
super-admin e o Sistema Principal com dados de demonstração):

```bash
cd backend
python seed.py
```

## Endpoints novos

| Método | Rota | Quem | Descrição |
|---|---|---|---|
| `POST` | `/api/auth/login` | público | `{codigo?, usuario, senha}` → token + usuário |
| `GET` | `/api/sistemas` | super-admin | lista sistemas (com contagens) |
| `POST` | `/api/sistemas` | super-admin | cria sistema + seu admin |
| `DELETE` | `/api/sistemas/{id}` | super-admin | exclui o sistema e **todos** os seus dados |
| `GET` | `/api/funcionarios` | admin | equipe do sistema (estatísticas) |
| `POST` | `/api/funcionarios` | admin | cria operador `{nome, username, senha}` |
| `DELETE` | `/api/funcionarios/{id}` | admin | remove operador (sem movimentações) |

Todos os endpoints de domínio (`/api/produtos`, `/api/movimentacoes`,
`/api/categorias`, `/api/fornecedores`, `/api/dashboard`) passaram a ser
**escopados automaticamente** pelo sistema do usuário logado. O super-admin é
bloqueado (403) nesses endpoints — ele gerencia sistemas, não estoque.

## Isolamento (como funciona)

Todas as tabelas de domínio ganharam a coluna `sistema_id`. Cada consulta filtra por
`sistema_id = usuário_logado.sistema_id`. SKU de produto e nome de categoria agora são
únicos **por sistema** (dois sistemas podem ter o mesmo SKU). O isolamento é validado
em teste E2E: um admin de outro sistema vê **0 produtos** do Sistema Principal.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `JWT_SECRET_KEY` | dev fallback | segredo do JWT (defina em produção) |
| `JWT_EXPIRE_MINUTES` | `480` | validade do token |
| `SUPERADMIN_SENHA` | `super123` | senha do super-admin criado na migração/seed |

## Como rodar

```bash
cd backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --host 127.0.0.1
# Acesse http://127.0.0.1:8000  (NÃO use Live Server / file:// — as chamadas /api falham)
```

> **Sobre o "bug" de não conseguir registrar movimentação / mexer no estoque:** o código
> sempre esteve correto; o sintoma vinha de **cache antigo do navegador** ou de abrir o
> frontend fora do servidor (`:5500`/`file://`). A v2.0 reescreveu a camada de login/JS,
> o que força o navegador a baixar os arquivos novos. Se algum dia reaparecer, faça
> **Ctrl+Shift+R** (hard refresh) e confirme que a URL é `http://127.0.0.1:8000`.
