const loadAIRecords = async () => {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_URL}/violations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const list = await response.json();
        
        const tbody = document.getElementById('ai-records-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const aiList = list.filter(v => v.reporter_name === 'Hệ thống AI' || v.status !== 'pending' || v.created_at);

        if (aiList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-gray-500">Chưa ghi nhận quét vi phạm nào từ AI.</td></tr>`;
            return;
        }

        aiList.forEach(v => {
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
                <td class="p-4"><img src="${v.annotated_url || v.image_url}" class="w-16 h-10 object-cover rounded cursor-pointer border border-white/10" onclick="showModal('${v.annotated_url || v.image_url}')"></td>
                <td class="p-4 font-mono font-bold text-white">${v.vehicle_plate}</td>
                <td class="p-4">${v.violation_type}</td>
                <td class="p-4 font-mono text-xs text-blue-400 font-bold">${(v.confidence * 100).toFixed(0)}%</td>
                <td class="p-4 text-xs text-gray-400">${new Date(v.created_at).toLocaleString('vi-VN')}</td>
                <td class="p-4">${statusBadge}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error(e);
    }
};

window.showModal = (src) => {
    const modal = document.getElementById('image-modal');
    const img = document.getElementById('modal-img');
    if (modal && img) {
        img.src = src;
        modal.classList.remove('hidden');
    }
};

window.closeModal = () => {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
};
