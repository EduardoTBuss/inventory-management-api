/**
 * movimentacoes.js — Register and list stock movements.
 */

let state = {
    page: 1,
    size: 20,
    produto_id: '',
    tipo: '',
    total: 0,
    pages: 0,
    produtos: [],
};

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;
    initUserUI();

    await loadProdutosSelect();
    await loadMovimentacoes();

    setupFilters();
    setupForm();
});

// ─── Produtos select ──────────────────────────────────────────────────────────

async function loadProdutosSelect() {
    try {
        // Carrega TODOS os produtos para o select.
        // O backend limita size a 100 (le=100), então paginamos em vez de
        // pedir uma página gigante — pedir size=200 retornava 422 e deixava
        // os selects vazios.
        const PAGE_SIZE = 100;
        const first = await apiFetch(`/api/produtos?page=1&size=${PAGE_SIZE}`);
        let produtos = first.items || [];

        for (let page = 2; page <= (first.pages || 1); page++) {
            const next = await apiFetch(`/api/produtos?page=${page}&size=${PAGE_SIZE}`);
            produtos = produtos.concat(next.items || []);
        }

        state.produtos = produtos;

        const selects = ['field-produto', 'filter-produto'];
        selects.forEach(id => {
            const sel = document.getElementById(id);
            if (!sel) return;
            const baseOpt = id === 'filter-produto'
                ? '<option value="">Todos os produtos</option>'
                : '<option value="">Selecione um produto</option>';
            sel.innerHTML = baseOpt + state.produtos.map(p =>
                `<option value="${p.id}" data-qtd="${p.quantidade}">${escapeHtml(p.nome)} (SKU: ${escapeHtml(p.sku)})</option>`
            ).join('');
        });
    } catch (err) {
        showToast('Erro ao carregar produtos: ' + err.message, 'error');
    }
}

// ─── Data loading ─────────────────────────────────────────────────────────────

async function loadMovimentacoes() {
    setTableLoading(true);
    try {
        const params = new URLSearchParams({ page: state.page, size: state.size });
        if (state.produto_id) params.set('produto_id', state.produto_id);
        if (state.tipo) params.set('tipo', state.tipo);

        const data = await apiFetch(`/api/movimentacoes?${params}`);
        state.total = data.total;
        state.pages = data.pages;

        renderTable(data.items);
        renderPagination();
        updateTableInfo(data.total);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function setTableLoading(loading) {
    const tbody = document.getElementById('mov-tbody');
    if (!tbody || !loading) return;
    tbody.innerHTML = Array(5).fill(`
        <tr>${Array(6).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}</tr>
    `).join('');
}

function updateTableInfo(total) {
    const el = document.getElementById('table-info');
    if (el) el.textContent = `${formatNumber(total)} movimentaç${total !== 1 ? 'ões' : 'ão'}`;
}

// ─── Table rendering ──────────────────────────────────────────────────────────

function renderTable(items) {
    const tbody = document.getElementById('mov-tbody');
    if (!tbody) return;

    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/>
                        </svg>
                        <p class="empty-title">Nenhuma movimentação encontrada</p>
                        <p class="empty-sub">Registre a primeira movimentação pelo formulário ao lado.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = items.map(m => `
        <tr>
            <td class="cell-mono cell-dim">${formatDate(m.criado_em)}</td>
            <td>
                <div class="cell-strong">${escapeHtml(m.produto_nome || '—')}</div>
            </td>
            <td>${getTipoBadge(m.tipo)}</td>
            <td>${getQuantidadeDisplay(m.tipo, m.quantidade)}</td>
            <td class="cell-dim" style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${m.motivo ? escapeHtml(m.motivo) : '<span style="color:var(--line-2);">—</span>'}</td>
            <td class="cell-dim">${escapeHtml(m.usuario_nome || '—')}</td>
        </tr>
    `).join('');
}

function getTipoBadge(tipo) {
    const map = {
        entrada: `<span class="badge badge-green">
            <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" d="M12 4v16m-8-8h16"/></svg>
            Entrada
        </span>`,
        saida: `<span class="badge badge-red">
            <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" d="M4 12h16"/></svg>
            Saída
        </span>`,
        ajuste: `<span class="badge badge-yellow">
            <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" d="M4 4l16 16M20 4L4 20"/></svg>
            Ajuste
        </span>`,
    };
    return map[tipo] || `<span class="badge badge-gray">${escapeHtml(tipo)}</span>`;
}

function getQuantidadeDisplay(tipo, qtd) {
    const colors = { entrada: 'var(--green)', saida: 'var(--red)', ajuste: 'var(--amber)' };
    const prefixes = { entrada: '+', saida: '−', ajuste: '±' };
    const color = colors[tipo] || 'var(--ink-2)';
    const prefix = prefixes[tipo] || '';
    return `<span class="t-mono" style="color:${color};font-weight:600;font-size:0.9375rem;">${prefix}${formatNumber(qtd)}</span>`;
}

// ─── Pagination ───────────────────────────────────────────────────────────────

function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container) return;

    if (state.pages <= 1) { container.innerHTML = ''; return; }

    let html = `<button class="page-btn" onclick="goToPage(${state.page - 1})" ${state.page <= 1 ? 'disabled' : ''} aria-label="Anterior">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
    </button>`;

    const range = getPaginationRange(state.page, state.pages);
    range.forEach(p => {
        if (p === '...') {
            html += `<span class="page-btn" style="cursor:default;border:none;">…</span>`;
        } else {
            html += `<button class="page-btn ${p === state.page ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>`;
        }
    });

    html += `<button class="page-btn" onclick="goToPage(${state.page + 1})" ${state.page >= state.pages ? 'disabled' : ''} aria-label="Próxima">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>
    </button>`;

    container.innerHTML = html;
}

function getPaginationRange(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    if (current <= 4) return [1, 2, 3, 4, 5, '...', total];
    if (current >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
    return [1, '...', current - 1, current, current + 1, '...', total];
}

function goToPage(page) {
    if (page < 1 || page > state.pages) return;
    state.page = page;
    loadMovimentacoes();
}

// ─── Filters ──────────────────────────────────────────────────────────────────

function setupFilters() {
    const filterProduto = document.getElementById('filter-produto');
    const filterTipo = document.getElementById('filter-tipo');
    const btnClear = document.getElementById('btn-clear-filters');

    if (filterProduto) {
        filterProduto.addEventListener('change', () => {
            state.produto_id = filterProduto.value;
            state.page = 1;
            loadMovimentacoes();
        });
    }

    if (filterTipo) {
        filterTipo.addEventListener('change', () => {
            state.tipo = filterTipo.value;
            state.page = 1;
            loadMovimentacoes();
        });
    }

    if (btnClear) {
        btnClear.addEventListener('click', () => {
            if (filterProduto) filterProduto.value = '';
            if (filterTipo) filterTipo.value = '';
            state.produto_id = '';
            state.tipo = '';
            state.page = 1;
            loadMovimentacoes();
        });
    }
}

// ─── Register form ────────────────────────────────────────────────────────────

function setupForm() {
    const form = document.getElementById('form-movimentacao');
    const tipoSelect = document.getElementById('field-tipo');
    const tipoIndicator = document.getElementById('tipo-indicator');

    if (tipoSelect) {
        tipoSelect.addEventListener('change', () => {
            updateTipoUI(tipoSelect.value);
        });
    }

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

function updateTipoUI(tipo) {
    const indicator = document.getElementById('tipo-indicator');
    if (!indicator) return;

    const configs = {
        entrada: { color: 'var(--green)', bg: 'var(--green-bg)', label: 'Entrada de estoque' },
        saida:   { color: 'var(--red)',   bg: 'var(--red-bg)',   label: 'Saída de estoque' },
        ajuste:  { color: 'var(--amber)', bg: 'var(--amber-bg)', label: 'Ajuste de inventário' },
    };

    const cfg = configs[tipo];
    if (!cfg) {
        indicator.style.display = 'none';
        return;
    }

    indicator.style.display = 'flex';
    indicator.style.background = cfg.bg;
    indicator.style.color = cfg.color;
    indicator.style.borderColor = 'currentColor';
    indicator.querySelector('span').textContent = cfg.label;
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-registrar');
    setButtonLoading(btn, true);

    const produtoId = document.getElementById('field-produto').value;
    const tipo = document.getElementById('field-tipo').value;
    const quantidade = parseInt(document.getElementById('field-quantidade').value);
    const motivo = document.getElementById('field-motivo').value.trim();

    if (!produtoId || !tipo || !quantidade || quantidade <= 0) {
        showToast('Preencha todos os campos obrigatórios.', 'error');
        setButtonLoading(btn, false);
        return;
    }

    const body = {
        produto_id: parseInt(produtoId),
        tipo,
        quantidade,
        motivo: motivo || null,
    };

    try {
        await apiFetch('/api/movimentacoes', { method: 'POST', body: JSON.stringify(body) });
        showToast('Movimentação registrada com sucesso!', 'success');
        document.getElementById('form-movimentacao').reset();
        document.getElementById('tipo-indicator').style.display = 'none';
        state.page = 1;
        await Promise.all([loadProdutosSelect(), loadMovimentacoes()]);
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
