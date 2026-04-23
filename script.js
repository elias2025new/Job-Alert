document.addEventListener('DOMContentLoaded', () => {
    const statusText = document.querySelector('.status-text');
    const keywordsList = document.getElementById('keywords-list');
    const lastResult = document.getElementById('last-result');
    const scanBtn = document.getElementById('scan-btn');
    const btnText = scanBtn.querySelector('.btn-text');
    const loader = scanBtn.querySelector('.loader');
    const toast = document.getElementById('toast');

    // --- Utility Functions ---
    const showToast = (message, type = 'success') => {
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    };

    const updateStatus = (status) => {
        statusText.textContent = status === 'online' ? 'Bot Active' : 'Offline';
        const pulse = document.querySelector('.pulse');
        pulse.style.backgroundColor = status === 'online' ? 'var(--success)' : 'var(--error)';
        pulse.style.animation = status === 'online' ? 'pulse-green 2s infinite' : 'none';
    };

    // --- API Interactions ---
    async function fetchBotData() {
        try {
            const response = await fetch('/api/data');
            if (!response.ok) throw new Error('Failed to fetch bot data');
            
            const data = await response.json();
            
            // Update UI
            updateStatus(data.status);
            
            // Keywords
            keywordsList.innerHTML = '';
            data.keywords.forEach(kw => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.textContent = kw;
                keywordsList.appendChild(span);
            });

            // Last Scan Result
            if (data.last_scan_result && data.last_scan_result.length > 0) {
                lastResult.innerHTML = `<p>Found: <span class="match-item">${data.last_scan_result.join(', ')}</span></p>`;
            } else {
                lastResult.innerHTML = '<p class="empty-state">No jobs found in last scan</p>';
            }

        } catch (error) {
            console.error(error);
            showToast('Connection error. Check console.', 'error');
            updateStatus('offline');
        }
    }

    async function triggerScan() {
        scanBtn.disabled = true;
        btnText.textContent = 'Scanning...';
        loader.classList.remove('hidden');

        try {
            const response = await fetch('/api/run', { method: 'POST' });
            if (!response.ok) throw new Error('Scan failed');
            
            const result = await response.json();
            
            if (result.success) {
                if (result.new_alert_sent) {
                    showToast('🚨 New jobs found! Alert sent to Telegram.');
                } else if (result.found_keywords.length > 0) {
                    showToast('Jobs found, but no new changes since last scan.');
                } else {
                    showToast('Scan complete. No matching jobs found.');
                }
                
                // Refresh data to show latest state
                await fetchBotData();
            } else {
                showToast(result.error || 'Scan encountered an error.', 'error');
            }
        } catch (error) {
            console.error(error);
            showToast('Failed to trigger scan.', 'error');
        } finally {
            scanBtn.disabled = false;
            btnText.textContent = 'Trigger Manual Scan';
            loader.classList.add('hidden');
        }
    }

    // --- Initialization ---
    fetchBotData();
    scanBtn.addEventListener('click', triggerScan);
});
