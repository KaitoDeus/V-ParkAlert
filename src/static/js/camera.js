window.playCameraInDashboard = (youtubeId) => {
    currentVideoId = youtubeId;
    const simCameraSelect = document.getElementById('sim-camera-id');
    if (simCameraSelect) {
        if (youtubeId === 'sJvEFrG0wq0') {
            simCameraSelect.value = '1';
        } else if (youtubeId === 'oif_zZFIfB4') {
            simCameraSelect.value = '2';
        } else if (youtubeId === '1EamsYw_Xyo') {
            simCameraSelect.value = '3';
        } else if (youtubeId === 'NeJGBQAY-bE') {
            simCameraSelect.value = '4';
        }
    }
    switchTab('authority-live');
    setTimeout(() => {
        loadPlayerStream();
    }, 300);
};

window.togglePlayerMode = (mode) => {
    playerMode = mode;
    const btnLive = document.getElementById('btn-player-live');
    const btnAi = document.getElementById('btn-player-ai');
    if (btnLive) btnLive.className = mode === 'live' ? 'px-3 py-1.5 rounded-lg bg-blue-600 text-white' : 'px-3 py-1.5 rounded-lg text-gray-400';
    if (btnAi) btnAi.className = mode === 'ai' ? 'px-3 py-1.5 rounded-lg bg-blue-600 text-white' : 'px-3 py-1.5 rounded-lg text-gray-400';
    
    const iframe = document.getElementById('live-player-iframe');
    const hud = document.getElementById('ai-hud-container');

    if (iframe && hud) {
        if (mode === 'live') {
            iframe.classList.remove('hidden');
            hud.classList.add('hidden');
        } else {
            iframe.classList.add('hidden');
            hud.classList.remove('hidden');
        }
    }
};

const loadPlayerStream = () => {
    const iframe = document.getElementById('live-player-iframe');
    const placeholder = document.getElementById('player-placeholder');
    if (!iframe || !placeholder) return;
    
    placeholder.classList.add('hidden');
    iframe.src = `https://www.youtube.com/embed/${currentVideoId}?autoplay=1&mute=1&controls=0&showinfo=0&rel=0`;
    iframe.classList.remove('hidden');
    
    const simCameraSelect = document.getElementById('sim-camera-id');
    if (simCameraSelect) {
        if (currentVideoId === 'sJvEFrG0wq0') {
            simCameraSelect.value = '1';
        } else if (currentVideoId === 'oif_zZFIfB4') {
            simCameraSelect.value = '2';
        } else if (currentVideoId === '1EamsYw_Xyo') {
            simCameraSelect.value = '3';
        } else if (currentVideoId === 'NeJGBQAY-bE') {
            simCameraSelect.value = '4';
        }
    }
    
    togglePlayerMode('live');
};

window.triggerSimulation = async () => {
    const token = localStorage.getItem('token');
    const cameraId = parseInt(document.getElementById('sim-camera-id').value);
    const violationType = document.getElementById('sim-violation-type').value;
    const alertBox = document.getElementById('sim-alert');

    try {
        const response = await fetch(`${API_URL}/camera/simulate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                camera_id: cameraId,
                violation_type: violationType
            })
        });

        if (!response.ok) {
            throw new Error('Kích hoạt mô phỏng thất bại');
        }

        if (alertBox) {
            alertBox.className = 'p-3 rounded-lg text-xs bg-green-950/40 text-green-400 border border-green-800/30 mb-4 animate-pulse';
            alertBox.innerHTML = `<i class="fa-solid fa-circle-check"></i> Đã kích hoạt mô phỏng vi phạm đỗ xe! Hệ thống AI đang quét luồng...`;
            alertBox.classList.remove('hidden');

            setTimeout(() => {
                alertBox.classList.add('hidden');
            }, 4000);
        }
    } catch (err) {
        alert(err.message);
    }
};

const loadCameraStatus = async () => {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`${API_URL}/camera/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await res.json();
        list.forEach(cam => {
            const badge = document.getElementById(`cam-status-badge-${cam.id}`);
            const btn = document.getElementById(`btn-cam-toggle-${cam.id}`);
            if (badge && btn) {
                if (cam.is_active) {
                    badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-green-950/60 text-green-400 border border-green-800/40';
                    badge.innerText = 'Active';
                    btn.className = 'px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/20 rounded-lg text-xs font-semibold';
                    btn.innerText = 'Tắt Camera';
                } else {
                    badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-red-950/60 text-red-400 border border-red-800/40';
                    badge.innerText = 'Inactive';
                    btn.className = 'px-3 py-1.5 bg-green-600/20 hover:bg-green-600/30 text-green-400 border border-green-500/20 rounded-lg text-xs font-semibold';
                    btn.innerText = 'Bật Camera';
                }
            }
        });
    } catch (e) {
        console.error(e);
    }
};

window.toggleCameraState = async (camId) => {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`${API_URL}/camera/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await res.json();
        const cam = list.find(c => String(c.id) === String(camId));
        if (!cam) return;
        
        const response = await fetch(`${API_URL}/camera/${camId}/control`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_active: !cam.is_active
            })
        });

        if (response.ok) {
            loadCameraStatus();
        }
    } catch (e) {
        console.error(e);
    }
};
