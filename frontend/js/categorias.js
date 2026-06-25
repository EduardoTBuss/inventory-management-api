/**
 * categorias.js — Full CRUD for product categories.
 */

let state = {
    items: [],
    editingId: null,
};

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;
    initUserUI();

    await loadCategorias();
    setupModal();
    setupAdminUI();
});

// ─── Data loading ─────────────────────────────────────────────────────────────

async function loadCategorias() {
    setTableLoading(true);
    try {
        const data = await apiFetch('/api/categorias');
        state.items = data || [];
        renderTable(state.items);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ─── Table ────────────────────────────────────────────────────────────────────

function setTableLoading(loading) {
    const tbody = document.getElementById('cat-tbody');
    if (!tbody || !loading) return;
    tbody.innerHTML = Array(4).fill(`
        <tr>${Array(3).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}</tr>
    `).join('');
}

function renderTable(items) {
    const tbody = document.getElementById('cat-tbody');
    if (!tbody) return;

    const countEl = document.getElementById('cat-count');
    if (countEl) countEl.textContent = `${items.length} categori${items.length !== 1 ? 'as' : 'a'}`;

    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3">
                    <div class="empty-state">
                        <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                        </svg>
                        <p class="empty-title">Nenhuma categoria cadastrada</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    const admin = isAdmin();

    tbody.innerHTML = items.map(c => `
        <tr>
            <td class="cell-strong">${escapeHtml(c.nome)}</td>
            <td class="cell-dim" style="font-size:0.875rem;">${c.descricao ? escapeHtml(c.descricao) : '<span style="color:var(--line-2);">—</span>'}</td>
            <td>
                <div style="display:flex;gap:0.375rem;">
                    ${admin ? `
                    <button class="btn-icon" onclick="openEditModal(${c.id})" data-tooltip="Editar" aria-label="Editar ${escapeHtml(c.nome)}">
                        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    </button>
                    <button class="btn-icon danger" onclick="confirmDelete(${c.id}, '${escapeHtml(c.nome)}')" data-tooltip="Excluir" aria-label="Excluir ${escapeHtml(c.nome)}">
                        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                    ` : '<span style="color:var(--ink-3);font-size:0.75rem;">—</span>'}
                </div>
            </td>
        </tr>
    `).join('');
}

// ─── Modal ────────────────────────────────────────────────────────────────────

function setupModal() {
    const overlay = document.getElementById('modal-categoria');
    const form = document.getElementById('form-categoria');
    const btnClose = document.getElementById('modal-close');
    const btnCancel = document.getElementById('btn-cancel');

    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    if (form) form.addEventListener('submit', handleSubmit);
}

function openCreateModal() {
    state.editingId = null;
    document.getElementById('modal-title').textContent = 'Nova Categoria';
    document.getElementById('form-categoria').reset();
    openModal();
}

function openEditModal(id) {
    const cat = state.items.find(c => c.id === id);
    if (!cat) return;

    state.editingId = id;
    document.getElementById('modal-title').textContent = 'Editar Categoria';
    document.getElementById('field-nome').value = cat.nome;
    document.getElementById('field-descricao').value = cat.descricao || '';
    openModal();
}

function openModal() {
    const overlay = document.getElementById('modal-categoria');
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
        const first = overlay.querySelector('input');
        if (first) first.focus();
    }, 100);
}

function closeModal() {
    const overlay = document.getElementById('modal-categoria');
    overlay.classList.remove('open');
    setTimeout(() => {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }, 200);
}

async function handleSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-save');
    setButtonLoading(btn, true);

    const body = {
        nome: document.getElementById('field-nome').value.trim(),
        descricao: document.getElementById('field-descricao').value.trim() || null,
    };

    if (!body.nome) {
        showToast('O nome da categoria é obrigatório.', 'error');
        setButtonLoading(btn, false);
        return;
    }

    try {
        if (state.editingId) {
            await apiFetch(`/api/categorias/${state.editingId}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Categoria atualizada!', 'success');
        } else {
            await apiFetch('/api/categorias', { method: 'POST', body: JSON.stringify(body) });
            showToast('Categoria criada!', 'success');
        }
        closeModal();
        await loadCategorias();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmDelete(id, nome) {
    if (!confirm(`Excluir a categoria "${nome}"?\n\nProdutos associados perderão a referência.`)) return;

    try {
        await apiFetch(`/api/categorias/${id}`, { method: 'DELETE' });
        showToast('Categoria excluída.', 'success');
        await loadCategorias();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function setupAdminUI() {
    const btn = document.getElementById('btn-nova-categoria');
    if (btn) {
        if (isAdmin()) {
            btn.style.display = '';
            btn.addEventListener('click', openCreateModal);
        } else {
            btn.style.display = 'none';
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
