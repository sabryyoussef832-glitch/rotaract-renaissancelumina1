(function () {
    const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : '';

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
        
        // Insert before the loginLink (Hello User)
        navList.insertBefore(settingsItem, loginLink.parentElement);
    }

    async function hydrateNavbarAuth() {
        const loginLink = document.querySelector('a.login-btn');
        const registerLink = document.querySelector('a.register-btn');
        if (!loginLink || !registerLink) return;

        // 1. Get cached user for immediate display
        let user = getStoredUser();
        
        // 2. If we have a cached user, show it immediately to avoid delay
        if (user && user.name) {
            updateNavbarWithUser(user, loginLink, registerLink);
        }

        // 3. Fetch from server in background to sync/verify
        const serverUser = await fetchCurrentUser();
        
        // Handle sync between server and cache
        if (serverUser) {
            // If server data is different or we didn't have a user, update UI again
            if (!user || user.name !== serverUser.name || user.role !== serverUser.role) {
                updateNavbarWithUser(serverUser, loginLink, registerLink);
            }
        } else {
            // If server says no user, but we had one in cache, clear it (session expired)
            if (user && window.location.protocol !== 'file:') {
                localStorage.removeItem('luminaUser');
                window.location.reload(); // Reload to show login/register buttons
            }
        }
    }

    function updateNavbarWithUser(user, loginLink, registerLink) {
        if (!user || !user.name) return;

        // Ensure Admin/Settings links exist
        ensureAdminLink(user, loginLink);
        ensureSettingsLink(user, loginLink);

        // Update Login button to show name
        loginLink.textContent = `Hello, ${shortenName(user.name)}`;
        loginLink.href = '#';
        loginLink.style.cursor = 'default';
        loginLink.onclick = (e) => e.preventDefault();

        // Update Register button to Logout
        registerLink.textContent = 'LOGOUT';
        registerLink.href = '#';
        registerLink.classList.remove('register-btn');
        registerLink.classList.add('login-btn');
        registerLink.style.background = '#2d3436';
        
        // Re-add logout listener (remove old one first to avoid duplicates)
        const newRegisterLink = registerLink.cloneNode(true);
        registerLink.parentNode.replaceChild(newRegisterLink, registerLink);
        
        newRegisterLink.addEventListener('click', async function (event) {
            event.preventDefault();
            await logout(true);
        });
    }

    document.addEventListener('DOMContentLoaded', hydrateNavbarAuth);
})();
