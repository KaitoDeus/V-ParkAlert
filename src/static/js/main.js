const loadComponents = async () => {
    try {
        // Load sidebar
        const sidebarRes = await fetch('/static/components/sidebar.html');
        if (sidebarRes.ok) {
            document.getElementById('sidebar-wrapper').innerHTML = await sidebarRes.text();
        }

        // Load modals
        const modalRes = await fetch('/static/components/image-modal.html');
        if (modalRes.ok) {
            document.getElementById('modal-wrapper').innerHTML = await modalRes.text();
        }

        // Load tab views
        const tabs = [
            'citizen-report', 'citizen-history',
            'authority-analytics', 'authority-live', 'authority-verify',
            'ai-control', 'ai-records'
        ];

        for (const tab of tabs) {
            const res = await fetch(`/static/components/${tab}.html`);
            if (res.ok) {
                const el = document.getElementById(`tab-${tab}`);
                if (el) el.innerHTML = await res.text();
            }
        }

        // Once components are loaded, verify auth and initialize the UI
        await checkAuth();

        // Switch to default tab depending on user role
        const role = localStorage.getItem('role');
        currentRole = role;
        if (role === 'citizen') {
            switchTab('citizen-report');
        } else if (role === 'authority') {
            switchTab('authority-analytics');
        } else if (role === 'ai_system') {
            switchTab('ai-control');
        }
    } catch (e) {
        console.error("Failed to load components:", e);
    }
};

window.switchTab = (tabId) => {
    // Hide all tabs
    const allTabs = [
        'citizen-report', 'citizen-history',
        'authority-analytics', 'authority-live', 'authority-verify',
        'ai-control', 'ai-records'
    ];

    allTabs.forEach(id => {
        const el = document.getElementById(`tab-${id}`);
        if (el) el.classList.add('hidden');
        
        const btn = document.getElementById(`btn-${id}`);
        if (btn) btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabId}`);
    if (selectedTab) selectedTab.classList.remove('hidden');

    const selectedBtn = document.getElementById(`btn-${tabId}`);
    if (selectedBtn) selectedBtn.classList.add('active');

    // Trigger tab-specific loaders
    if (tabId === 'citizen-report') {
        initCitizenMap();
        setupFileInput();
    } else if (tabId === 'citizen-history') {
        loadCitizenHistory();
    } else if (tabId === 'authority-analytics') {
        initAnalyticsMap();
        loadAnalytics();
    } else if (tabId === 'authority-live') {
        // Safe play stream
        loadPlayerStream();
    } else if (tabId === 'authority-verify') {
        loadVerifyList();
    } else if (tabId === 'ai-control') {
        loadCameraStatus();
    } else if (tabId === 'ai-records') {
        loadAIRecords();
    }
};

// Start initialization on DOM content loaded
window.addEventListener('DOMContentLoaded', () => {
    loadComponents();
});
