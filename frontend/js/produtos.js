/**
 * produtos.js — Full CRUD for products with pagination, search and category filter.
 */

let state = {
    page: 1,
    size: 20,
    q: '',
    categoria_id: '',
    total: 0,
    pages: 0,
    categorias: [],
    fornecedores: [],
    editingId: null,
};

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;
    initUserUI();

    await Promise.all([loadCategorias(), loadFornecedores()]);
    await loadProdutos();

    setupSearch();
    setupModal();
    setupAdminUI();
});

// ─── Data loading ─────────────────────────────────────────────────────────────

async function loadProdutos() {
    setTableLoading(true);
    try {
        const params = new URLSearchParams({ page: state.page, size: state.size });
        if (state.q) params.set('q', state.q);
        if (state.categoria_id) params.set('categoria_id', state.categoria_id);

        const data = await apiFetch(`/api/produtos?${params}`);
        state.total = data.total;
        state.pages = data.pages;

        renderTable(data.items);
        renderPagination();
        renderTableInfo(data.total, data.page, data.pages, data.items.length);
    } catch (err) {
        showToast(err.message, 'error');
        setTableLoading(false);
    }
}

async function loadCategorias() {
    try {
        state.categorias = await apiFetch('/api/categorias') || [];
        populateCategoriaFilters();
    } catch {
        state.categorias = [];
    }
}

async function loadFornecedores() {
    try {
        state.fornecedores = await apiFetch('/api/fornecedores') || [];
    } catch {
        state.fornecedores = [];
    }
}

function populateCategoriaFilters() {
    const filterSelect = document.getElementById('filter-categoria');
    const modalSelect = document.getElementById('field-categoria');

    const options = state.categorias.map(c =>
        `<option value="${c.id}">${escapeHtml(c.nome)}</option>`
    ).join('');

    if (filterSelect) {
        filterSelect.innerHTML = `<option value="">Todas as categorias</option>` + options;
    }
    if (modalSelect) {
        modalSelect.innerHTML = `<option value="">Selecione uma categoria</option>` + options;
    }

    // Populate fornecedores in modal
    const fornSelect = document.getElementById('field-fornecedor');
    if (fornSelect) {
        fornSelect.innerHTML = `<option value="">Nenhum</option>` +
            state.fornecedores.map(f => `<option value="${f.id}">${escapeHtml(f.nome)}</option>`).join('');
    }
}

// ─── Table rendering ──────────────────────────────────────────────────────────

function setTableLoading(loading) {
    const tbody = document.getElementById('produtos-tbody');
    if (!tbody) return;
    if (loading) {
        tbody.innerHTML = Array(5).fill(`
            <tr>
                ${Array(6).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}
            </tr>
        `).join('');
    }
}

function renderTable(items) {
    const tbody = document.getElementById('produtos-tbody');
    if (!tbody) return;

    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"/>
                        </svg>
                        <p class="empty-title">Nenhum produto encontrado</p>
                        <p class="empty-sub">Tente ajustar os filtros ou cadastre um novo produto.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    const admin = isAdmin();

    tbody.innerHTML = items.map(p => {
        const abaixo = p.quantidade < p.qtd_minima;
        const estoqueBadge = abaixo
            ? `<span class="badge badge-red"><span class="stock-dot" style="background:currentColor;"></span>${formatNumber(p.quantidade)}</span>`
            : `<span class="badge badge-green"><span class="stock-dot" style="background:currentColor;"></span>${formatNumber(p.quantidade)}</span>`;

        const acoes = admin ? `
            <button class="btn-icon" onclick="openEditModal(${p.id})" data-tooltip="Editar" aria-label="Editar ${escapeHtml(p.nome)}">
                <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            </button>
            <button class="btn-icon danger" onclick="confirmDelete(${p.id}, '${escapeHtml(p.nome)}')" data-tooltip="Excluir" aria-label="Excluir ${escapeHtml(p.nome)}">
                <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
        ` : `<span style="color:var(--ink-3);font-size:0.75rem;">—</span>`;

        return `
            <tr>
                <td>
                    <div class="cell-strong">${escapeHtml(p.nome)}</div>
                    ${p.fornecedor_nome ? `<div style="font-size:0.75rem;color:var(--ink-3);">${escapeHtml(p.fornecedor_nome)}</div>` : ''}
                </td>
                <td class="cell-mono">${escapeHtml(p.sku)}</td>
                <td>${p.categoria_nome ? `<span class="badge badge-blue">${escapeHtml(p.categoria_nome)}</span>` : '<span style="color:var(--ink-3);">—</span>'}</td>
                <td>${estoqueBadge}<span class="t-mono" style="font-size:0.6875rem;color:var(--ink-3);margin-left:0.375rem;">/ mín ${p.qtd_minima}</span></td>
                <td class="cell-mono" style="font-weight:600;color:var(--ink);">${formatCurrency(p.preco_venda)}</td>
                <td>
                    <div style="display:flex;gap:0.375rem;align-items:center;">
                        ${acoes}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function renderTableInfo(total, page, pages, count) {
    const el = document.getElementById('table-info');
    if (el) {
        el.textContent = `${formatNumber(total)} produto${total !== 1 ? 's' : ''} encontrado${total !== 1 ? 's' : ''}`;
    }
}

function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container) return;

    if (state.pages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `
        <button class="page-btn" onclick="goToPage(${state.page - 1})" ${state.page <= 1 ? 'disabled' : ''} aria-label="Página anterior">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
    `;

    const range = getPaginationRange(state.page, state.pages);
    range.forEach(p => {
        if (p === '...') {
            html += `<span class="page-btn" style="cursor:default;border:none;">…</span>`;
        } else {
            html += `<button class="page-btn ${p === state.page ? 'active' : ''}" onclick="goToPage(${p})" aria-label="Página ${p}" aria-current="${p === state.page ? 'page' : 'false'}">${p}</button>`;
        }
    });

    html += `
        <button class="page-btn" onclick="goToPage(${state.page + 1})" ${state.page >= state.pages ? 'disabled' : ''} aria-label="Próxima página">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>
        </button>
    `;

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
    loadProdutos();
}

// ─── Search & Filter ──────────────────────────────────────────────────────────

let searchTimeout = null;

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const filterCategoria = document.getElementById('filter-categoria');

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                state.q = searchInput.value.trim();
                state.page = 1;
                loadProdutos();
            }, 400);
        });
    }

    if (filterCategoria) {
        filterCategoria.addEventListener('change', () => {
            state.categoria_id = filterCategoria.value;
            state.page = 1;
            loadProdutos();
        });
    }
}

// ─── Modal ────────────────────────────────────────────────────────────────────

function setupModal() {
    const overlay = document.getElementById('modal-produto');
    const form = document.getElementById('form-produto');
    const btnClose = document.getElementById('modal-close');
    const btnCancel = document.getElementById('btn-cancel');

    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (overlay) {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) closeModal();
        });
    }

    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

function openCreateModal() {
    state.editingId = null;
    document.getElementById('modal-title').textContent = 'Novo Produto';
    document.getElementById('form-produto').reset();
    populateCategoriaFilters();
    openModal();
}

async function openEditModal(id) {
    state.editingId = id;
    document.getElementById('modal-title').textContent = 'Editar Produto';

    try {
        // Find from existing data or fetch
        const data = await apiFetch(`/api/produtos/${id}`);
        fillForm(data);
        openModal();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function fillForm(produto) {
    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val ?? '';
    };
    set('field-nome', produto.nome);
    set('field-sku', produto.sku);
    set('field-preco-custo', produto.preco_custo);
    set('field-preco-venda', produto.preco_venda);
    set('field-qtd-minima', produto.qtd_minima);
    set('field-categoria', produto.categoria_id);
    set('field-fornecedor', produto.fornecedor_id || '');
    set('field-imagem', produto.imagem_url || '');
}

function openModal() {
    const overlay = document.getElementById('modal-produto');
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
    // Focus first input
    setTimeout(() => {
        const first = overlay.querySelector('input:not([disabled])');
        if (first) first.focus();
    }, 100);
}

function closeModal() {
    const overlay = document.getElementById('modal-produto');
    overlay.classList.remove('open');
    setTimeout(() => {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }, 200);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-save');
    setButtonLoading(btn, true);

    const body = {
        nome: document.getElementById('field-nome').value.trim(),
        sku: document.getElementById('field-sku').value.trim(),
        preco_custo: parseFloat(document.getElementById('field-preco-custo').value) || 0,
        preco_venda: parseFloat(document.getElementById('field-preco-venda').value) || 0,
        qtd_minima: parseInt(document.getElementById('field-qtd-minima').value) || 0,
        categoria_id: parseInt(document.getElementById('field-categoria').value),
        fornecedor_id: document.getElementById('field-fornecedor').value
            ? parseInt(document.getElementById('field-fornecedor').value)
            : null,
        imagem_url: document.getElementById('field-imagem').value.trim() || null,
    };

    try {
        if (state.editingId) {
            await apiFetch(`/api/produtos/${state.editingId}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Produto atualizado com sucesso!', 'success');
        } else {
            await apiFetch('/api/produtos', { method: 'POST', body: JSON.stringify(body) });
            showToast('Produto criado com sucesso!', 'success');
        }
        closeModal();
        await loadProdutos();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmDelete(id, nome) {
    if (!confirm(`Excluir o produto "${nome}"?\n\nEsta ação não pode ser desfeita.`)) return;

    try {
        await apiFetch(`/api/produtos/${id}`, { method: 'DELETE' });
        showToast('Produto excluído.', 'success');
        if (state.page > 1 && document.querySelectorAll('#produtos-tbody tr').length === 1) {
            state.page--;
        }
        await loadProdutos();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function setupAdminUI() {
    const btnNovo = document.getElementById('btn-novo-produto');
    if (btnNovo) {
        if (isAdmin()) {
            btnNovo.style.display = '';
            btnNovo.addEventListener('click', openCreateModal);
        } else {
            btnNovo.style.display = 'none';
        }
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
