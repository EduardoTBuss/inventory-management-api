/**
 * sidebar.js — Injects the sidebar HTML and handles mobile toggle.
 * Include this script in every protected page before closing </body>.
 * Set window.ACTIVE_NAV to the current page key before including.
 *
 * Multi-tenant:
 *   - super-admin: vê apenas "Sistemas".
 *   - admin/operador: vê o menu do estoque; "Equipe" só para admin.
 *   - O nome do sistema aparece no rodapé da marca.
 */

(function () {
    const user = (typeof getCurrentUser === 'function') ? getCurrentUser() : null;
    const papel = user ? user.papel : null;

    const ICONS = {
        sistemas: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><path d="M7 7h.01M7 17h.01"/></svg>`,
        dashboard: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
        produtos: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"/></svg>`,
        movimentacoes: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/></svg>`,
        categorias: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg>`,
        fornecedores: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0H5m14 0h2m-2 0h-2M5 21H3m2 0h2M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>`,
        funcionarios: `<svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4zm6 0a3 3 0 10-2.5-4.66"/></svg>`,
    };

    let NAV_ITEMS;
    if (papel === 'superadmin') {
        NAV_ITEMS = [
            { key: 'sistemas', label: 'Sistemas', href: '/sistemas.html', icon: ICONS.sistemas },
        ];
    } else {
        NAV_ITEMS = [
            { key: 'dashboard', label: 'Dashboard', href: '/dashboard.html', icon: ICONS.dashboard },
            { key: 'produtos', label: 'Produtos', href: '/produtos.html', icon: ICONS.produtos },
            { key: 'movimentacoes', label: 'Movimentações', href: '/movimentacoes.html', icon: ICONS.movimentacoes },
            { key: 'categorias', label: 'Categorias', href: '/categorias.html', icon: ICONS.categorias },
            { key: 'fornecedores', label: 'Fornecedores', href: '/fornecedores.html', icon: ICONS.fornecedores },
            { key: 'funcionarios', label: 'Equipe', href: '/funcionarios.html', adminOnly: true, icon: ICONS.funcionarios },
        ];
    }

    const userIsAdmin = (typeof isAdmin === 'function') ? isAdmin() : false;
    const visibleItems = NAV_ITEMS.filter(item => !item.adminOnly || userIsAdmin);

    const activeKey = window.ACTIVE_NAV || '';

    const navItemsHTML = visibleItems.map(item => `
        <li>
            <a href="${item.href}" class="sidebar-nav-item ${item.key === activeKey ? 'active' : ''}" aria-current="${item.key === activeKey ? 'page' : 'false'}">
                ${item.icon}
                <span>${item.label}</span>
            </a>
        </li>
    `).join('');

    // Rodapé da marca: nome do sistema (ou "Plataforma" para super-admin)
    const brandSub = papel === 'superadmin'
        ? 'Plataforma · super-admin'
        : (user && user.sistema_nome ? escapeBrand(user.sistema_nome) : 'Livro de inventário');

    const sidebarHTML = `
        <div class="sidebar-overlay" id="sidebar-overlay" aria-hidden="true"></div>
        <nav class="sidebar" id="sidebar" aria-label="Navegação principal">
            <div class="sidebar-brand">
                <div class="brand-name">Estoque<em>.</em></div>
                <div class="brand-sub">${brandSub}</div>
            </div>

            <ul class="sidebar-nav">
                ${navItemsHTML}
            </ul>

            <div class="sidebar-footer">
                <div class="sidebar-user">
                    <div class="sidebar-user-avatar" id="sidebar-user-avatar" aria-hidden="true">&middot;</div>
                    <div style="min-width:0;">
                        <div id="sidebar-user-name">Carregando...</div>
                        <div id="sidebar-user-role"></div>
                    </div>
                </div>
                <button id="btn-logout" class="sidebar-logout" aria-label="Sair do sistema">
                    <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                    Sair
                </button>
            </div>
        </nav>
    `;

    function escapeBrand(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    const placeholder = document.getElementById('sidebar-placeholder');
    if (placeholder) {
        placeholder.outerHTML = sidebarHTML;
    } else {
        document.body.insertAdjacentHTML('afterbegin', sidebarHTML);
    }

    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        });
    }
    if (overlay) overlay.addEventListener('click', closeSidebar);
})();
