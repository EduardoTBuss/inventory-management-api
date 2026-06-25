/**
 * dashboard.js — Loads and renders all dashboard data.
 */

async function loadDashboard() {
    try {
        const data = await apiFetch('/api/dashboard');
        renderMetrics(data);
        renderMovimentacoesRecentes(data.movimentacoes_recentes || []);
        renderProdutosAbaixoMinimo(data.produtos_abaixo_minimo || []);
        renderBarChart(data.mais_movimentados || []);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderMetrics(data) {
    const setValue = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setValue('metric-produtos', formatNumber(data.total_produtos));
    setValue('metric-categorias', formatNumber(data.total_categorias));
    setValue('metric-valor', formatCurrency(data.valor_total_estoque));
    setValue('metric-limite', formatNumber((data.produtos_abaixo_minimo || []).length));

    // Remove skeleton loaders
    document.querySelectorAll('.metric-skeleton').forEach(el => el.remove());
    document.querySelectorAll('.metric-value').forEach(el => el.style.display = '');
}

function renderMovimentacoesRecentes(items) {
    const tbody = document.getElementById('movimentacoes-tbody');
    if (!tbody) return;

    if (items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    <svg width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                    <p>Nenhuma movimentação recente.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = items.map(m => {
        const tipoBadge = getTipoBadge(m.tipo);
        return `
            <tr>
                <td class="cell-strong" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(m.produto_nome || '—')}</td>
                <td>${tipoBadge}</td>
                <td class="cell-mono" style="font-weight:600;color:var(--ink);">${formatNumber(m.quantidade)}</td>
                <td class="cell-mono cell-dim">${formatDate(m.criado_em)}</td>
            </tr>
        `;
    }).join('');
}

function renderProdutosAbaixoMinimo(items) {
    const container = document.getElementById('produtos-limite-list');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="padding:2rem;">
                <svg width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <p style="margin-top:0.5rem;font-size:0.875rem;">Todos os produtos estão com estoque adequado.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = items.map(p => {
        const pct = p.qtd_minima > 0 ? Math.min(100, Math.round((p.quantidade / p.qtd_minima) * 100)) : 0;
        return `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:0.8125rem 1.25rem;border-bottom:1px solid var(--line);">
                <div style="min-width:0;flex:1;">
                    <a href="/produtos.html" style="font-size:0.875rem;font-weight:600;color:var(--ink);text-decoration:none;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(p.nome)}">${escapeHtml(p.nome)}</a>
                    <span class="t-mono" style="font-size:0.6875rem;color:var(--ink-3);">${p.quantidade} de ${p.qtd_minima} mínimo</span>
                </div>
                <span class="badge badge-red" style="margin-left:0.75rem;flex-shrink:0;">${pct}%</span>
            </div>
        `;
    }).join('');
}

function renderBarChart(items) {
    const container = document.getElementById('bar-chart');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = `<p style="color:var(--ink-3);font-size:0.875rem;text-align:center;padding:1.5rem 0;">Nenhum dado disponível.</p>`;
        return;
    }

    const max = Math.max(...items.map(i => i.total_movimentacoes), 1);

    container.innerHTML = items.slice(0, 8).map(item => {
        const pct = Math.round((item.total_movimentacoes / max) * 100);
        return `
            <div class="bar-row">
                <span class="bar-label" title="${escapeHtml(item.produto_nome)}">${escapeHtml(item.produto_nome)}</span>
                <div class="bar-track" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100">
                    <div class="bar-fill" style="width:${pct}%"></div>
                </div>
                <span class="bar-value">${formatNumber(item.total_movimentacoes)}</span>
            </div>
        `;
    }).join('');
}

function getTipoBadge(tipo) {
    const map = {
        entrada: `<span class="badge badge-green"><span class="stock-dot" style="background:currentColor;"></span>Entrada</span>`,
        saida:   `<span class="badge badge-red"><span class="stock-dot" style="background:currentColor;"></span>Saída</span>`,
        ajuste:  `<span class="badge badge-yellow"><span class="stock-dot" style="background:currentColor;"></span>Ajuste</span>`,
    };
    return map[tipo] || `<span class="badge badge-gray">${escapeHtml(tipo)}</span>`;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', () => {
    if (!guardAuth()) return;
    initUserUI();
    loadDashboard();
});
