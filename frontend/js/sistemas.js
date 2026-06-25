/**
 * sistemas.js — Painel do SUPER-ADMIN: listar, criar e excluir sistemas (tenants).
 *
 * Dupla barreira: front redireciona não-superadmin; back exige require_superadmin.
 */

let sistemas = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;

    if (!isSuperadmin()) {
        showToast('Área restrita ao super-administrador.', 'error');
        setTimeout(() => { window.location.href = '/dashboard.html'; }, 1200);
        return;
    }

    initUserUI();
    setupModal();
    document.getElementById('btn-novo-sistema').addEventListener('click', openCreateModal);
    await loadSistemas();
});

async function loadSistemas() {
    setTableLoading(true);
    try {
        const data = await apiFetch('/api/sistemas');
        if (!data) return;
        sistemas = data;
        renderTable(sistemas);
        updateInfo(sistemas.length);
    } catch (err) {
        showToast(err.message, 'error');
        renderError();
    }
}

function setTableLoading(loading) {
    const tbody = document.getElementById('sistemas-tbody');
    if (!tbody || !loading) return;
    tbody.innerHTML = Array(3).fill(
        `<tr>${Array(7).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}</tr>`
    ).join('');
}

function updateInfo(total) {
    const el = document.getElementById('table-info');
    if (el) el.textContent = `${formatNumber(total)} sistema${total !== 1 ? 's' : ''}`;
}

function renderError() {
    const tbody = document.getElementById('sistemas-tbody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">
            <p class="empty-title">Não foi possível carregar os sistemas</p>
            <p class="empty-sub">Tente recarregar a página.</p>
        </div></td></tr>`;
    }
}

function renderTable(items) {
    const tbody = document.getElementById('sistemas-tbody');
    if (!tbody) return;

    if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">
            <p class="empty-title">Nenhum sistema cadastrado</p>
            <p class="empty-sub">Crie o primeiro sistema pelo botão "Novo sistema".</p>
        </div></td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(s => `
        <tr>
            <td><div class="cell-strong">${escapeHtml(s.nome)}</div></td>
            <td><span class="badge badge-blue t-mono">${escapeHtml(s.codigo)}</span></td>
            <td>
                ${s.admin_nome ? `<div class="cell-strong" style="font-size:0.8125rem;">${escapeHtml(s.admin_nome)}</div>
                   <div class="cell-dim t-mono" style="font-size:0.75rem;">${escapeHtml(s.admin_username || '')}</div>`
                  : '<span style="color:var(--ink-3);">— sem admin —</span>'}
            </td>
            <td style="text-align:right;"><span class="t-mono">${formatNumber(s.total_usuarios)}</span></td>
            <td style="text-align:right;"><span class="t-mono">${formatNumber(s.total_produtos)}</span></td>
            <td class="cell-dim">${formatDate(s.criado_em)}</td>
            <td>
                <button class="btn-icon danger" onclick="confirmDelete(${s.id}, '${escapeHtml(s.nome)}', ${s.total_produtos}, ${s.total_usuarios})" data-tooltip="Excluir" aria-label="Excluir ${escapeHtml(s.nome)}">
                    <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
            </td>
        </tr>
    `).join('');
}

// ─── Modal ──────────────────────────────────────────────────────────────────

function setupModal() {
    const overlay = document.getElementById('modal-sistema');
    const form = document.getElementById('form-sistema');
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('btn-cancel').addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    form.addEventListener('submit', handleSubmit);

    // Auto-slug do código a partir do nome (só enquanto o usuário não editar o código).
    const nome = document.getElementById('field-nome');
    const codigo = document.getElementById('field-codigo');
    let codigoTocado = false;
    codigo.addEventListener('input', () => { codigoTocado = true; });
    nome.addEventListener('input', () => {
        if (!codigoTocado) codigo.value = slugify(nome.value);
    });
}

function slugify(s) {
    return String(s).toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9\s-]/g, '')
        .trim().replace(/\s+/g, '-').replace(/-+/g, '-');
}

function openCreateModal() {
    document.getElementById('form-sistema').reset();
    openModal();
}

function openModal() {
    const overlay = document.getElementById('modal-sistema');
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
    setTimeout(() => document.getElementById('field-nome').focus(), 100);
}

function closeModal() {
    const overlay = document.getElementById('modal-sistema');
    overlay.classList.remove('open');
    setTimeout(() => { overlay.style.display = 'none'; document.body.style.overflow = ''; }, 200);
}

async function handleSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-save');
    setButtonLoading(btn, true);

    const body = {
        nome: document.getElementById('field-nome').value.trim(),
        codigo: document.getElementById('field-codigo').value.trim().toLowerCase(),
        admin_nome: document.getElementById('field-admin-nome').value.trim(),
        admin_username: document.getElementById('field-admin-username').value.trim().toLowerCase(),
        admin_senha: document.getElementById('field-admin-senha').value,
        admin_email: document.getElementById('field-admin-email').value.trim() || null,
    };

    if (!body.nome || !body.codigo || !body.admin_nome || !body.admin_username || !body.admin_senha) {
        showToast('Preencha todos os campos obrigatórios.', 'error');
        setButtonLoading(btn, false);
        return;
    }

    try {
        await apiFetch('/api/sistemas', { method: 'POST', body: JSON.stringify(body) });
        showToast(`Sistema "${body.nome}" criado com sucesso!`, 'success');
        closeModal();
        await loadSistemas();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmDelete(id, nome, totalProdutos, totalUsuarios) {
    const aviso = (totalProdutos > 0 || totalUsuarios > 1)
        ? `\n\nATENÇÃO: isto apaga ${totalProdutos} produto(s), ${totalUsuarios} usuário(s) e TODAS as movimentações deste sistema.`
        : '';
    if (!confirm(`Excluir o sistema "${nome}"?${aviso}\n\nEsta ação não pode ser desfeita.`)) return;

    try {
        await apiFetch(`/api/sistemas/${id}`, { method: 'DELETE' });
        showToast('Sistema excluído.', 'success');
        await loadSistemas();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
