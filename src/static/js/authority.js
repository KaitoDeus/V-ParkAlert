// Initialize Map for Authority
const initAnalyticsMap = async () => {
    if (analyticsMap) {
        analyticsMap.invalidateSize();
        return;
    }

    analyticsMap = L.map('analytics-map').setView([10.7745, 106.7025], 14);
    
    const isLight = document.body.classList.contains('light-mode');
    const tileUrl = isLight 
        ? 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png' 
        : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

    analyticsTileLayer = L.tileLayer(tileUrl, {
        maxZoom: 19
    }).addTo(analyticsMap);

    await renderAnalyticsMarkers();
};

const renderAnalyticsMarkers = async () => {
    // Clear existing markers
    mapMarkers.forEach(m => analyticsMap.removeLayer(m));
    mapMarkers = [];

    try {
        const token = localStorage.getItem('token');
        // Get camera points
        const camRes = await fetch(`${API_URL}/camera/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const cameras = await camRes.json();

        // Get violation points
        const violRes = await fetch(`${API_URL}/violations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const violations = await violRes.json();

        // Add cameras
        cameras.forEach(cam => {
            const icon = L.divIcon({
                html: `<div class="w-8 h-8 rounded-full bg-indigo-500/20 border-2 border-indigo-400 flex items-center justify-center shadow-lg"><i class="fa-solid fa-video text-xs text-indigo-300"></i></div>`,
                className: '',
                iconSize: [32, 32]
            });
            const marker = L.marker([cam.latitude, cam.longitude], { icon }).addTo(analyticsMap);
            
            marker.bindPopup(`
                <div class="p-2 text-slate-900 font-sans">
                    <h4 class="font-bold text-sm">${cam.name}</h4>
                    <p class="text-xs text-gray-500">Trạng thái: ${cam.is_active ? 'Hoạt động' : 'Tắt'}</p>
                    <button onclick="playCameraInDashboard('${cam.youtube_id}')" class="mt-2 w-full py-1 text-center text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded font-semibold transition-all">Xem luồng trực tiếp</button>
                </div>
            `);
            mapMarkers.push(marker);
        });

        // Add violations
        violations.forEach(v => {
            if (v.status !== 'approved') return;
            const icon = L.divIcon({
                html: `<div class="w-8 h-8 rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center animate-pulse"><i class="fa-solid fa-circle-exclamation text-xs text-red-400"></i></div>`,
                className: '',
                iconSize: [32, 32]
            });
            const marker = L.marker([v.latitude, v.longitude], { icon }).addTo(analyticsMap);
            marker.bindPopup(`
                <div class="p-1 text-slate-900 font-sans">
                    <h4 class="font-bold text-xs text-red-600">${v.violation_type}</h4>
                    <p class="text-[10px] text-gray-600">Biển số: <b>${v.vehicle_plate}</b></p>
                </div>
            `);
            mapMarkers.push(marker);
        });
    } catch (e) {
        console.error(e);
    }
};

// Load Analytics View
const loadAnalytics = async () => {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/violations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await response.json();

        // Compute metrics
        const total = list.length;
        const pending = list.filter(v => v.status === 'pending').length;
        const approved = list.filter(v => v.status === 'approved').length;
        const rejected = list.filter(v => v.status === 'rejected').length;

        // Update KPI text
        document.getElementById('kpi-total').innerText = total;
        document.getElementById('kpi-pending').innerText = pending;
        document.getElementById('kpi-approved').innerText = approved;
        document.getElementById('kpi-rejected').innerText = rejected;

        // Refresh markers on analytics map
        if (analyticsMap) {
            renderAnalyticsMarkers();
        }
    } catch (e) {
        console.error(e);
    }
};

// Load Authority Verify List
const loadVerifyList = async () => {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/violations?status_filter=pending`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await response.json();

        const tbody = document.getElementById('pending-violations-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-500">Không có báo cáo vi phạm nào cần phê duyệt.</td></tr>`;
            return;
        }

        list.forEach(v => {
            const row = document.createElement('tr');
            row.className = 'border-b border-white/5 hover:bg-white/5 transition-all';
            row.innerHTML = `
                <td class="p-4"><img src="${v.annotated_url || v.image_url}" class="w-16 h-10 object-cover rounded cursor-pointer border border-white/10" onclick="showModal('${v.annotated_url || v.image_url}')"></td>
                <td class="p-4 font-mono font-bold text-white">${v.vehicle_plate}</td>
                <td class="p-4">${v.violation_type}</td>
                <td class="p-4 text-xs font-semibold text-blue-400">${v.reporter_name || 'Cư dân'}</td>
                <td class="p-4 text-xs text-gray-400">${new Date(v.created_at).toLocaleString('vi-VN')}</td>
                <td class="p-4">
                    <div class="flex gap-2">
                        <button onclick="verifyViolation(${v.id}, 'approved')" class="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded text-xs font-bold transition-all"><i class="fa-solid fa-check"></i> Duyệt</button>
                        <button onclick="verifyViolation(${v.id}, 'rejected')" class="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-bold transition-all"><i class="fa-solid fa-xmark"></i> Từ chối</button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error(e);
    }
};

// Approve/Reject Action
window.verifyViolation = async (violationId, status) => {
    const token = localStorage.getItem('token');
    const alertBox = document.getElementById('verify-alert');
    
    try {
        const response = await fetch(`${API_URL}/violations/${violationId}/status`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: status,
                admin_notes: `Đã xác thực bởi Cảnh sát vào lúc ${new Date().toLocaleString('vi-VN')}`
            })
        });

        if (!response.ok) {
            throw new Error('Cập nhật trạng thái không thành công');
        }

        if (alertBox) {
            alertBox.className = 'p-3 rounded-lg text-xs bg-green-950/40 text-green-400 border border-green-800/30 mb-4';
            alertBox.innerText = `Đã cập nhật trạng thái báo cáo thành công!`;
            alertBox.classList.remove('hidden');
            setTimeout(() => {
                alertBox.classList.add('hidden');
            }, 3000);
        }

        loadVerifyList();
    } catch (err) {
        alert(err.message);
    }
};
