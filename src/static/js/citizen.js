// Initialize Map for citizen upload tab
const initCitizenMap = () => {
    if (citizenMap) return;
    
    // Central Da Nang position default
    const defaultPos = [16.0544, 108.2022]; 
    citizenMap = L.map('citizen-map').setView(defaultPos, 13);
    
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const darkUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const lightUrl = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
    const tileUrl = savedTheme === 'light' ? lightUrl : darkUrl;

    citizenTileLayer = L.tileLayer(tileUrl, {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(citizenMap);

    citizenMarker = L.marker(defaultPos, { draggable: true }).addTo(citizenMap);
    
    // Sync values to form input
    const syncLatLng = (lat, lng) => {
        document.getElementById('report-lat').value = lat.toFixed(6);
        document.getElementById('report-lng').value = lng.toFixed(6);
    };

    syncLatLng(defaultPos[0], defaultPos[1]);

    // Dragged marker
    citizenMarker.on('dragend', function (e) {
        const pos = citizenMarker.getLatLng();
        syncLatLng(pos.lat, pos.lng);
    });

    // Map click
    citizenMap.on('click', function (e) {
        citizenMarker.setLatLng(e.latlng);
        syncLatLng(e.latlng.lat, e.latlng.lng);
    });
};

// Citizen File Drag & Drop / AI inference pipeline
const setupFileInput = () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('report-file');
    const preview = document.getElementById('image-preview');
    const placeholder = document.getElementById('dropzone-placeholder');
    const overlay = document.getElementById('scanning-overlay');

    if (!dropzone || !fileInput) return;

    dropzone.onclick = () => fileInput.click();

    dropzone.ondragover = (e) => {
        e.preventDefault();
        dropzone.className = 'border-2 border-dashed border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-white/5 relative overflow-hidden h-[200px]';
    };

    dropzone.ondragleave = () => {
        dropzone.className = 'border-2 border-dashed border-white/10 hover:border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all hover:bg-white/5 relative overflow-hidden h-[200px]';
    };

    dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.className = 'border-2 border-dashed border-white/10 hover:border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all hover:bg-white/5 relative overflow-hidden h-[200px]';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            processImageFile(e.dataTransfer.files[0]);
        }
    };

    fileInput.onchange = () => {
        if (fileInput.files && fileInput.files[0]) {
            processImageFile(fileInput.files[0]);
        }
    };
};

const processImageFile = async (file) => {
    const preview = document.getElementById('image-preview');
    const placeholder = document.getElementById('dropzone-placeholder');
    const overlay = document.getElementById('scanning-overlay');

    // Show local image preview immediately
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        placeholder.classList.add('hidden');
    };
    reader.readAsDataURL(file);

    // Show scanning overlay
    overlay.classList.remove('hidden');

    // Upload & trigger AI detection API
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/violations/upload-scan`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            const errorDetails = await response.json();
            throw new Error(errorDetails.detail || 'Không thể quét ảnh bằng chứng');
        }

        const data = await response.json();
        
        // Show detected bounding boxes / populated data fields
        document.getElementById('report-plate').value = data.vehicle_plate || '';
        document.getElementById('report-violation').value = data.violation_type || 'Đỗ xe đè vỉa hè';
        if (data.annotated_url) {
            // Update preview source to show annotated image with boxes
            preview.src = data.annotated_url;
        }
        
        // Alert scanned successfully
        const reportAlert = document.getElementById('report-alert');
        reportAlert.className = 'p-4 rounded-xl text-sm bg-green-950/40 text-green-400 border border-green-800/30 flex items-center gap-2';
        reportAlert.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>Quét AI hoàn tất! Phát hiện xe ${data.vehicle_plate || 'Không rõ biển'} với độ tin cậy ${(data.confidence * 100).toFixed(0)}%.</span>`;
        reportAlert.classList.remove('hidden');
    } catch (err) {
        const reportAlert = document.getElementById('report-alert');
        reportAlert.className = 'p-4 rounded-xl text-sm bg-red-950/40 text-red-400 border border-red-800/30 flex items-center gap-2';
        reportAlert.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> <span>Quét AI thất bại: ${err.message}</span>`;
        reportAlert.classList.remove('hidden');
    } finally {
        overlay.classList.add('hidden');
    }
};

// Submit Citizen Report
window.submitReport = async () => {
    const token = localStorage.getItem('token');
    const fileInput = document.getElementById('report-file');
    const reportAlert = document.getElementById('report-alert');

    const plate = document.getElementById('report-plate').value.trim();
    const violation = document.getElementById('report-violation').value;
    const lat = parseFloat(document.getElementById('report-lat').value);
    const lng = parseFloat(document.getElementById('report-lng').value);
    const desc = document.getElementById('report-desc').value.trim();

    if (!fileInput.files || !fileInput.files[0]) {
        alert('Vui lòng chọn ảnh bằng chứng vi phạm');
        return;
    }

    // Upload payload
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('vehicle_plate', plate);
    formData.append('violation_type', violation);
    formData.append('latitude', lat);
    formData.append('longitude', lng);
    formData.append('description', desc);

    try {
        const response = await fetch(`${API_URL}/violations/report`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Gửi phản ánh vi phạm thất bại');
        }

        reportAlert.className = 'p-4 rounded-xl text-sm bg-green-950/40 text-green-400 border border-green-800/30 flex items-center gap-2';
        reportAlert.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>Cảm ơn bạn! Đã gửi báo cáo vi phạm thành công tới hệ thống.</span>`;
        reportAlert.classList.remove('hidden');

        // Clear input form
        document.getElementById('report-plate').value = '';
        document.getElementById('report-desc').value = '';
        document.getElementById('image-preview').classList.add('hidden');
        document.getElementById('dropzone-placeholder').classList.remove('hidden');
        fileInput.value = '';

        // Reload history
        loadCitizenHistory();
    } catch (err) {
        alert(err.message);
    }
};

// Load Citizen History list
const loadCitizenHistory = async () => {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/violations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await response.json();
        
        const tbody = document.getElementById('citizen-history-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        // Filter report generated by citizen role only (whose reporter is resident/citizen)
        const citizenList = list.filter(v => v.reporter_name !== 'Hệ thống AI');

        if (citizenList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-500">Bạn chưa gửi báo cáo vi phạm nào.</td></tr>`;
            return;
        }

        citizenList.forEach(v => {
            let statusBadge = '';
            if (v.status === 'pending') {
                statusBadge = `<span class="px-2 py-0.5 rounded text-xs bg-yellow-950/40 text-yellow-400 border border-yellow-800/20">Chờ duyệt</span>`;
            } else if (v.status === 'approved') {
                statusBadge = `<span class="px-2 py-0.5 rounded text-xs bg-green-950/40 text-green-400 border border-green-800/20">Đã duyệt</span>`;
            } else {
                statusBadge = `<span class="px-2 py-0.5 rounded text-xs bg-red-950/40 text-red-400 border border-red-800/20">Từ chối</span>`;
            }

            const row = document.createElement('tr');
            row.className = 'border-b border-white/5 hover:bg-white/5 transition-all';
            row.innerHTML = `
                <td class="p-4"><img src="${v.image_url}" class="w-16 h-10 object-cover rounded cursor-pointer border border-white/10" onclick="showModal('${v.image_url}')"></td>
                <td class="p-4 font-mono font-bold text-white">${v.vehicle_plate || 'N/A'}</td>
                <td class="p-4">${v.violation_type}</td>
                <td class="p-4 text-xs font-mono text-gray-400">${v.latitude.toFixed(4)}, ${v.longitude.toFixed(4)}</td>
                <td class="p-4 text-xs text-gray-400">${new Date(v.created_at).toLocaleString('vi-VN')}</td>
                <td class="p-4">${statusBadge}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error(e);
    }
};
