(function () {
    const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';

    function getStoredUser() {
        try {
            return JSON.parse(localStorage.getItem('luminaUser') || 'null');
        } catch (error) {
            return null;
        }
    }

    function shortenName(name) {
        if (name.length <= 18) {
            return name;
        }
        return name.slice(0, 18) + '...';
    }

    function getMembersOnlyLinks() {
        return Array.from(document.querySelectorAll('a[href*="projects & Events.html"]'));
    }

    function syncMembersOnlyLinks(user) {
        getMembersOnlyLinks().forEach(function (link) {
            const container = link.closest('li') || link;
            container.style.display = '';
        });
    }

    async function fetchCurrentUser() {
        try {
            const response = await fetch(`${API_BASE}/api/me`, {
                credentials: 'include'
            });
            if (!response.ok) {
                return null;
            }
            const data = await response.json();
            if (data && data.user) {
                localStorage.setItem('luminaUser', JSON.stringify(data.user));
                return data.user;
            }
        } catch (error) {
            console.warn('Could not fetch current user from server:', error);
            return null;
        }
        return null;
    }

    function ensureAdminLink(user, loginLink) {
        if (!user || user.role !== 'admin' || !loginLink) {
            return;
        }

        const navList = loginLink.closest('ul');
        if (!navList || navList.querySelector('a[data-admin-link="true"]')) {
            return;
        }

        const adminItem = document.createElement('li');
        const adminLink = document.createElement('a');
        adminLink.href = 'admin.html';
        adminLink.textContent = 'Admin';
        adminLink.setAttribute('data-admin-link', 'true');
        adminItem.appendChild(adminLink);
        navList.insertBefore(adminItem, loginLink.parentElement);
    }

    async function logout(canManageAccount) {
        try {
            if (canManageAccount) {
                await fetch(`${API_BASE}/api/logout`, {
                    method: 'POST',
                    credentials: 'include'
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        }
        localStorage.removeItem('luminaUser');
        window.location.href = 'index.html';
    }

    function ensureSettingsLink(user, loginLink) {
        if (!user || !loginLink) {
            return;
        }

        const navList = loginLink.closest('ul');
        if (!navList || navList.querySelector('a[data-settings-link="true"]')) {
            return;
        }

        const settingsItem = document.createElement('li');
        const settingsLink = document.createElement('a');
        settingsLink.href = 'settings.html';
        settingsLink.innerHTML = '<i class="fas fa-bars"></i>';
        settingsLink.setAttribute('data-settings-link', 'true');
        settingsLink.title = 'Settings';
        settingsLink.style.fontSize = '1.2rem';
        settingsLink.style.color = 'var(--primary-pink)';
        settingsItem.appendChild(settingsLink);
        
        navList.insertBefore(settingsItem, loginLink.parentElement);
    }

    async function hydrateNavbarAuth() {
        const loginLink = document.querySelector('a.login-btn');
        const registerLink = document.querySelector('a.register-btn');
        if (!loginLink || !registerLink) return;

        let user = getStoredUser();
        
        if (user && user.name) {
            updateNavbarWithUser(user, loginLink, registerLink);
        }

        const serverUser = await fetchCurrentUser();
        
        if (serverUser) {
            if (!user || user.name !== serverUser.name || user.role !== serverUser.role) {
                updateNavbarWithUser(serverUser, loginLink, registerLink);
            }
        } else {
            if (user && window.location.protocol !== 'file:') {
                localStorage.removeItem('luminaUser');
                window.location.reload();
            }
        }
    }

    function updateNavbarWithUser(user, loginLink, registerLink) {
        if (!user || !user.name) return;

        ensureAdminLink(user, loginLink);
        ensureSettingsLink(user, loginLink);

        loginLink.textContent = `Hello, ${shortenName(user.name)}`;
        loginLink.href = '#';
        loginLink.style.cursor = 'default';
        loginLink.onclick = (e) => e.preventDefault();

        registerLink.textContent = 'LOGOUT';
        registerLink.href = '#';
        registerLink.classList.remove('register-btn');
        registerLink.classList.add('login-btn');
        registerLink.style.background = '#2d3436';
        
        const newRegisterLink = registerLink.cloneNode(true);
        registerLink.parentNode.replaceChild(newRegisterLink, registerLink);
        
        newRegisterLink.addEventListener('click', async function (event) {
            event.preventDefault();
            await logout(true);
        });
    }

    document.addEventListener('DOMContentLoaded', hydrateNavbarAuth);
})();