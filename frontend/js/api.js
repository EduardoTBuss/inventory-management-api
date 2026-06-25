/**
 * api.js — Central fetch wrapper for all API calls.
 * Handles auth headers, error parsing, 401 redirect, and toast notifications.
 */

// O frontend é servido pelo próprio FastAPI, então usamos caminho relativo
// (mesma origem). Antes estava fixo em "http://localhost:8000": se o servidor
// subisse em outra porta/host (ex.: uvicorn --port 8080), TODA chamada de API
// falhava com "Não foi possível conectar ao servidor". Relativo também evita
// preflight CORS desnecessário (localhost vs 127.0.0.1).
const API_BASE = '';

async function apiFetch(path, options = {}) {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let res;
    try {
        res = await fetch(API_BASE + path, { ...options, headers });
    } catch (networkError) {
        throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão.');
    }

    // 401 fora do login = sessão expirada → volta para a tela de login.
    // No próprio login, o 401 significa "credenciais inválidas" e precisa
    // chegar ao catch da página para a mensagem aparecer ao usuário.
    if (res.status === 401 && path !== '/api/auth/login') {
        logout();
        return;
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
        const message = Array.isArray(err.detail)
            ? err.detail.map(e => e.msg).join(', ')
            : (err.detail || 'Erro na requisição');
        throw new Error(message);
    }

    if (res.status === 204) return null;
    return res.json();
}

// ─── Toast System ────────────────────────────────────────────────────────────

let toastContainer = null;

function getToastContainer() {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 1.25rem;
            right: 1.25rem;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }
    return toastContainer;
}

function showToast(message, type = 'success') {
    const container = getToastContainer();

    const icons = {
        success: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>`,
        error:   `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>`,
        warning: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>`,
        info:    `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path stroke-linecap="round" d="M12 16v-4m0-4h.01"/></svg>`,
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${icons[type] ? type : 'info'}`;
    toast.innerHTML = `<span style="flex-shrink:0;display:flex;">${icons[type] || icons.info}</span><span>${message}</span>`;
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('show'));
    });

    // Animate out and remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 200);
    }, 3500);
}

// ─── Loading Button Helper ────────────────────────────────────────────────────

function setButtonLoading(btn, loading, originalText) {
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = `
            <svg class="animate-spin" style="display:inline;width:1rem;height:1rem;margin-right:0.375rem;vertical-align:middle" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="31.4" stroke-dashoffset="31.4" stroke-linecap="round">
                    <animateTransform attributeName="transform" type="rotate" dur="0.8s" repeatCount="indefinite" from="0 12 12" to="360 12 12"/>
                </circle>
            </svg>
            Aguarde...
        `;
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText || originalText || btn.innerHTML;
    }
}

// ─── Format Helpers ───────────────────────────────────────────────────────────

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
}

function formatDate(isoString) {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function formatNumber(value) {
    return new Intl.NumberFormat('pt-BR').format(value || 0);
}
