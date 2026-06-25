/**
 * funcionarios.js — Seção Equipe (RESTRITA A ADMIN), escopada ao sistema.
 *
 * Admin pode criar/excluir operadores do SEU sistema e ver o desempenho de todos.
 * Dupla barreira: front redireciona não-admin; back exige require_admin.
 */

let equipe = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!guardAuth()) return;

    if (!isAdmin()) {
        showToast('Acesso restrito a administradores.', 'error');
        setTimeout(() => { window.location.href = '/dashboard.html'; }, 1200);
        return;
    }

    initUserUI();
    setupModal();
    document.getElementById('btn-novo-operador').addEventListener('click', openCreateModal);
    await loadEquipe();
});

async function loadEquipe() {
    setTableLoading(true);
    try {
        const data = await apiFetch('/api/funcionarios');
        if (!data) return;
        equipe = data.funcionarios || [];
        renderTable(equipe);
        updateTableInfo(data.total_funcionarios || 0);
    } catch (err) {
        showToast(err.message, 'error');
        renderError();
    }
}

function setTableLoading(loading) {
    const tbody = document.getElementById('equipe-tbody');
    if (!tbody || !loading) return;
    tbody.innerHTML = Array(3).fill(
        `<tr>${Array(7).fill(`<td><div class="skeleton" style="height:1rem;"></div></td>`).join('')}</tr>`
    ).join('');
}

function updateTableInfo(total) {
    const el = document.getElementById('table-info');
    if (el) el.textContent = `${formatNumber(total)} funcionário${total !== 1 ? 's' : ''}`;
}

function renderError() {
    const tbody = document.getElementById('equipe-tbody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="7">
            <div class="empty-state">
                <p class="empty-title">Não foi possível carregar a equipe</p>
                <p class="empty-sub">Tente recarregar a página.</p>
            </div>
        </td></tr>`;
    }
}

function renderTable(funcionarios) {
    const tbody = document.getElementById('equipe-tbody');
    if (!tbody) return;

    if (funcionarios.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7">
            <div class="empty-state">
                <p class="empty-title">Nenhum funcionário encontrado</p>
                <p class="empty-sub">Crie um operador pelo botão "Novo operador".</p>
            </div>
        </td></tr>`;
        return;
    }

    const me = getCurrentUser();

    tbody.innerHTML = funcionarios.map(f => {
        const isOperador = f.papel === 'operador';
        const semMov = (f.total_movimentacoes || 0) === 0;
        const isSelf = me && me.id === f.id;
        const podeExcluir = isOperador && !isSelf;

        const acao = podeExcluir
            ? `<button class="btn-icon danger" onclick="confirmDelete(${f.id}, '${escapeHtml(f.nome)}', ${f.total_movimentacoes || 0})" data-tooltip="${semMov ? 'Excluir operador' : 'Possui movimentações'}" aria-label="Excluir ${escapeHtml(f.nome)}">
                <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
               </button>`
            : `<span style="color:var(--ink-3);font-size:0.75rem;">—</span>`;

        return `
        <tr>
            <td>
                <div class="cell-strong">${escapeHtml(f.nome)}</div>
                <div class="cell-dim t-mono" style="font-size:0.75rem;">${escapeHtml(f.username || '')}${f.email ? ' · ' + escapeHtml(f.email) : ''}</div>
            </td>
            <td>${getPapelBadge(f.papel)}</td>
            <td style="text-align:right;"><span class="t-mono" style="font-weight:600;">${formatNumber(f.total_vendido)}</span></td>
            <td style="text-align:right;"><span class="t-mono" style="font-weight:600;color:var(--green,#15803d);">${formatCurrency(f.total_faturado)}</span></td>
            <td style="text-align:right;"><span class="t-mono cell-dim">${formatNumber(f.total_movimentacoes)}</span></td>
            <td class="cell-dim">${f.ultima_atividade ? formatDate(f.ultima_atividade) : '<span style="color:var(--line-2);">— nunca —</span>'}</td>
            <td>${acao}</td>
        </tr>`;
    }).join('');
}

function getPapelBadge(papel) {
    if (papel === 'admin') return `<span class="badge badge-yellow">Administrador</span>`;
    return `<span class="badge badge-gray">Operador</span>`;
}

// ─── Modal Novo Operador ──────────────────────────────────────────────────────

function setupModal() {
    const overlay = document.getElementById('modal-operador');
    const form = document.getElementById('form-operador');
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('btn-cancel').addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
    form.addEventListener('submit', handleSubmit);

    const nome = document.getElementById('field-nome');
    const username = document.getElementById('field-username');
    let tocado = false;
    username.addEventListener('input', () => { tocado = true; });
    nome.addEventListener('input', () => {
        if (!tocado) username.value = slugify(nome.value);
    });
}

function slugify(s) {
    return String(s).toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9._-]/g, '');
}

function openCreateModal() {
    document.getElementById('form-operador').reset();
    openModal();
}

function openModal() {
    const overlay = document.getElementById('modal-operador');
    overlay.style.display = 'flex';
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
    setTimeout(() => document.getElementById('field-nome').focus(), 100);
}

function closeModal() {
    const overlay = document.getElementById('modal-operador');
    overlay.classList.remove('open');
    setTimeout(() => { overlay.style.display = 'none'; document.body.style.overflow = ''; }, 200);
}

async function handleSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-save');
    setButtonLoading(btn, true);

    const body = {
        nome: document.getElementById('field-nome').value.trim(),
        username: document.getElementById('field-username').value.trim().toLowerCase(),
        senha: document.getElementById('field-senha').value,
    };

    if (!body.nome || !body.username || !body.senha) {
        showToast('Preencha todos os campos.', 'error');
        setButtonLoading(btn, false);
        return;
    }

    try {
        await apiFetch('/api/funcionarios', { method: 'POST', body: JSON.stringify(body) });
        showToast(`Operador "${body.nome}" criado!`, 'success');
        closeModal();
        await loadEquipe();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

async function confirmDelete(id, nome, totalMov) {
    if (totalMov > 0) {
        showToast('Operador possui movimentações registradas e não pode ser excluído (trilha de auditoria).', 'error');
        return;
    }
    if (!confirm(`Excluir o operador "${nome}"?\n\nEsta ação não pode ser desfeita.`)) return;
    try {
        await apiFetch(`/api/funcionarios/${id}`, { method: 'DELETE' });
        showToast('Operador excluído.', 'success');
        await loadEquipe();
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
