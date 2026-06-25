/**
 * fornecedores.js — Full CRUD for suppliers.
 */

let state = {
    items: [],
    editingId: null,
};

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;
    initUserUI();

    await loadFornecedores();
    setupModal();
    setupAdminUI();
});

// ─── Data loading ─────────────────────────────────────────────────────────────

async function loadFornecedores() {
    setTableLoading(true);
    try {
        const data = await apiFetch('/api/fornecedores');
        state.items = data || [];
        renderTable(state.items);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ─── Table ────────────────────────────────────────────────────────────────────

function setTableLoading(loading) {
    const tbody = document.getElementById('forn-tbody');
    if (!tbody || !loading) return;
    tbody.innerHTML = Array(4).fill(`
        <tr>${Array(5).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}</tr>
    `).join('');
}

function renderTable(items) {
    const tbody = document.getElementById('forn-tbody');
    if (!tbody) return;

    const countEl = document.getElementById('forn-count');
    if (countEl) countEl.textContent = `${items.length} fornecedor${items.length !== 1 ? 'es' : ''}`;

    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0H5m14 0h2m-2 0h-2M5 21H3m2 0h2M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                        </svg>
                        <p class="empty-title">Nenhum fornecedor cadastrado</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    const admin = isAdmin();

    tbody.innerHTML = items.map(f => `
        <tr>
            <td class="cell-strong">${escapeHtml(f.nome)}</td>
            <td style="color:var(--ink-2);">${f.contato ? escapeHtml(f.contato) : '<span style="color:var(--line-2);">—</span>'}</td>
            <td>
                ${f.email
                    ? `<a href="mailto:${escapeHtml(f.email)}" class="t-mono" style="color:var(--accent-dark);text-decoration:none;font-size:0.8125rem;border-bottom:1px solid var(--line-2);">${escapeHtml(f.email)}</a>`
                    : '<span style="color:var(--line-2);">—</span>'
                }
            </td>
            <td class="cell-mono">${f.telefone ? escapeHtml(f.telefone) : '<span style="color:var(--line-2);">—</span>'}</td>
            <td>
                <div style="display:flex;gap:0.375rem;">
                    ${admin ? `
                    <button class="btn-icon" onclick="openEditModal(${f.id})" data-tooltip="Editar" aria-label="Editar ${escapeHtml(f.nome)}">
                        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    </button>
                    <button class="btn-icon danger" onclick="confirmDelete(${f.id}, '${escapeHtml(f.nome)}')" data-tooltip="Excluir" aria-label="Excluir ${escapeHtml(f.nome)}">
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
    const overlay = document.getElementById('modal-fornecedor');
    const form = document.getElementById('form-fornecedor');
    const btnClose = document.getElementById('modal-close');
    const btnCancel = document.getElementById('btn-cancel');

    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (btnCancel) btnCancel.addEventListener('click', closeModal);
    if (overlay) overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    if (form) form.addEventListener('submit', handleSubmit);
}

function openCreateModal() {
    state.editingId = null;
    document.getElementById('modal-title').textContent = 'Novo Fornecedor';
    document.getElementById('form-fornecedor').reset();
    openModal();
}

function openEditModal(id) {
    const forn = state.items.find(f => f.id === id);
    if (!forn) return;

    state.editingId = id;
    document.getElementById('modal-title').textContent = 'Editar Fornecedor';

    const set = (fieldId, val) => {
        const el = document.getElementById(fieldId);
        if (el) el.value = val || '';
    };
    set('field-nome', forn.nome);
    set('field-contato', forn.contato);
    set('field-email', forn.email);
    set('field-telefone', forn.telefone);

    openModal();
}

function openModal() {
    const overlay = document.getElementById('modal-fornecedor');
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
        const first = overlay.querySelector('input');
        if (first) first.focus();
    }, 100);
}

function closeModal() {
    const overlay = document.getElementById('modal-fornecedor');
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

    const nome = document.getElementById('field-nome').value.trim();
    if (!nome) {
        showToast('O nome do fornecedor é obrigatório.', 'error');
        setButtonLoading(btn, false);
        return;
    }

    const body = {
        nome,
        contato: document.getElementById('field-contato').value.trim() || null,
        email: document.getElementById('field-email').value.trim() || null,
        telefone: document.getElementById('field-telefone').value.trim() || null,
    };

    try {
        if (state.editingId) {
            await apiFetch(`/api/fornecedores/${state.editingId}`, { method: 'PUT', body: JSON.stringify(body) });
            showToast('Fornecedor atualizado!', 'success');
        } else {
            await apiFetch('/api/fornecedores', { method: 'POST', body: JSON.stringify(body) });
            showToast('Fornecedor criado!', 'success');
        }
        closeModal();
        await loadFornecedores();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmDelete(id, nome) {
    if (!confirm(`Excluir o fornecedor "${nome}"?\n\nProdutos associados perderão a referência.`)) return;

    try {
        await apiFetch(`/api/fornecedores/${id}`, { method: 'DELETE' });
        showToast('Fornecedor excluído.', 'success');
        await loadFornecedores();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function setupAdminUI() {
    const btn = document.getElementById('btn-novo-fornecedor');
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
