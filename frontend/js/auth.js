/**
 * auth.js — Authentication helpers (multi-tenant).
 *
 * Login agora usa: código do sistema (opcional p/ super-admin) + usuário + senha.
 */

function login(codigo, usuario, senha) {
    return apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ codigo: codigo || null, usuario, senha }),
    }).then(data => {
        if (!data) return;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('usuario', JSON.stringify(data.usuario));
        return data;
    });
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = '/login.html';
}

function getCurrentUser() {
    try {
        const raw = localStorage.getItem('usuario');
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function guardAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

function isAdmin() {
    const user = getCurrentUser();
    return user && user.papel === 'admin';
}

function isSuperadmin() {
    const user = getCurrentUser();
    return user && user.papel === 'superadmin';
}

/** Página de destino conforme o papel após o login. */
function homeForUser(user) {
    return user && user.papel === 'superadmin' ? '/sistemas.html' : '/dashboard.html';
}

function papelLabel(papel) {
    if (papel === 'superadmin') return 'Super-admin';
    if (papel === 'admin') return 'Administrador';
    return 'Operador';
}

/**
 * Populates sidebar user info and sets up logout button.
 * Call after DOM ready on every protected page.
 */
function initUserUI() {
    const user = getCurrentUser();
    if (!user) return;

    const nameEl = document.getElementById('sidebar-user-name');
    const roleEl = document.getElementById('sidebar-user-role');
    const avatarEl = document.getElementById('sidebar-user-avatar');
    const logoutBtn = document.getElementById('btn-logout');

    if (nameEl) nameEl.textContent = user.nome || user.username;
    if (roleEl) roleEl.textContent = papelLabel(user.papel);
    if (avatarEl) avatarEl.textContent = (user.nome || user.username || '?').charAt(0).toUpperCase();
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
}
