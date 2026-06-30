const checkAuth = async () => {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    const username = localStorage.getItem('username');

    if (!token || !role) {
        window.location.href = '/login';
        return;
    }

    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            localStorage.clear();
            window.location.href = '/login';
            return;
        }

        // Show/hide navigation tabs based on user role
        document.getElementById(`nav-group-${role}`).classList.remove('hidden');

        // Populate user info card
        document.getElementById('profile-name').innerText = username || 'User';
        document.getElementById('profile-initial').innerText = (username || 'U').charAt(0).toUpperCase();

        const roleText = role === 'citizen' ? 'Cư Dân' : role === 'authority' ? 'Cảnh Sát' : 'Hệ Thống AI';
        document.getElementById('role-badge').innerText = roleText;

        // Initialize Theme from storage
        const savedTheme = localStorage.getItem('theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
            document.getElementById('theme-icon-sidebar').className = 'fa-solid fa-sun text-xs';
            document.getElementById('theme-text-sidebar').innerText = 'Sáng';
        } else {
            document.body.classList.remove('light-mode');
            document.getElementById('theme-icon-sidebar').className = 'fa-solid fa-moon text-xs';
            document.getElementById('theme-text-sidebar').innerText = 'Tối';
        }
    } catch (err) {
        localStorage.clear();
        window.location.href = '/login';
    }
};

window.handleLogout = () => {
    const theme = localStorage.getItem('theme');
    localStorage.clear();
    if (theme) localStorage.setItem('theme', theme);
    window.location.href = '/login';
};

const setMapTheme = (theme) => {
    const darkUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const lightUrl = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    const url = theme === 'light' ? lightUrl : darkUrl;

    if (citizenMap) {
        if (citizenTileLayer) citizenMap.removeLayer(citizenTileLayer);
        citizenTileLayer = L.tileLayer(url, { maxZoom: 19 }).addTo(citizenMap);
    }
    if (analyticsMap) {
        if (analyticsTileLayer) analyticsMap.removeLayer(analyticsTileLayer);
        analyticsTileLayer = L.tileLayer(url, { maxZoom: 19 }).addTo(analyticsMap);
    }
};

window.toggleTheme = () => {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon-sidebar');
    const themeText = document.getElementById('theme-text-sidebar');
    
    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        if (themeIcon) themeIcon.className = 'fa-solid fa-moon text-xs';
        if (themeText) themeText.innerText = 'Tối';
        localStorage.setItem('theme', 'dark');
        setMapTheme('dark');
    } else {
        body.classList.add('light-mode');
        if (themeIcon) themeIcon.className = 'fa-solid fa-sun text-xs';
        if (themeText) themeText.innerText = 'Sáng';
        localStorage.setItem('theme', 'light');
        setMapTheme('light');
    }
};
