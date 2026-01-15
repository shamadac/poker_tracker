// Main application JavaScript
let handsFound = 0;
let currentConfig = {};

// Load initial config and status
async function loadStatus() {
    try {
        const configRes = await fetch('/api/config');
        currentConfig = await configRes.json();
        
        document.getElementById('player-name').textContent = currentConfig.username;
        document.getElementById('ai-provider').textContent = 
            currentConfig.ai_provider === 'ollama' ? 'Ollama (Local)' : 'Gemini (Cloud)';
        
        // Set radio buttons
        document.querySelector(`input[name="ai-provider"][value="${currentConfig.ai_provider}"]`).checked = true;
        
        // Set model selections
        document.getElementById('ollama-model').value = currentConfig.ollama_model;
        document.getElementById('gemini-model').value = currentConfig.gemini_model;
        
        // Show Gemini key status
        if (currentConfig.has_gemini_key) {
            document.getElementById('gemini-key-status').style.display = 'block';
            document.getElementById('gemini-api-key').placeholder = 'API key already configured (leave blank to keep)';
        }
        
        // Show/hide settings
        toggleProviderSettings(currentConfig.ai_provider);
        
        // Check AI status
        await checkAIStatus();
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

async function checkAIStatus() {
    try {
        const statusRes = await fetch('/api/ai/status');
        const status = await statusRes.json();
        const aiStatus = document.getElementById('ai-status');
        const ollamaDetail = document.getElementById('ollama-status-detail');
        const setupBtn = document.getElementById('setup-ollama-btn');
        
        if (status.ready) {
            aiStatus.textContent = '✓ Ready';
            aiStatus.style.color = '#28a745';
            
            if (currentConfig.ai_provider === 'ollama') {
                ollamaDetail.className = 'status-detail success';
                ollamaDetail.textContent = '✓ Ollama is ready with model: ' + currentConfig.ollama_model;
                setupBtn.style.display = 'none';
            }
        } else {
            aiStatus.textContent = '✗ Not Ready';
            aiStatus.style.color = '#dc3545';
            
            if (currentConfig.ai_provider === 'ollama') {
                ollamaDetail.className = 'status-detail warning';
                ollamaDetail.textContent = '⚠ ' + status.message;
                
                if (status.can_auto_install) {
                    setupBtn.style.display = 'block';
                    setupBtn.textContent = status.model_available === false ? 
                        'Install Model' : 'Install Ollama';
                }
            }
        }
    } catch (error) {
        console.error('Error checking AI status:', error);
    }
}

// Provider selection
document.querySelectorAll('input[name="ai-provider"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        toggleProviderSettings(e.target.value);
    });
});

function toggleProviderSettings(provider) {
    const ollamaSettings = document.getElementById('ollama-settings');
    const geminiSettings = document.getElementById('gemini-settings');
    
    if (provider === 'ollama') {
        ollamaSettings.style.display = 'block';
        geminiSettings.style.display = 'none';
    } else {
        ollamaSettings.style.display = 'none';
        geminiSettings.style.display = 'block';
    }
}

// Save settings
document.getElementById('save-settings-btn').addEventListener('click', async () => {
    const btn = document.getElementById('save-settings-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';
    
    const provider = document.querySelector('input[name="ai-provider"]:checked').value;
    const settings = {
        ai_provider: provider,
        ollama_model: document.getElementById('ollama-model').value,
        gemini_model: document.getElementById('gemini-model').value
    };
    
    // Only update API key if user entered a new one
    if (provider === 'gemini') {
        const apiKey = document.getElementById('gemini-api-key').value;
        if (apiKey && apiKey.trim() !== '') {
            settings.gemini_api_key = apiKey;
        }
    }
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            await loadStatus();
            alert('Settings saved successfully!');
        }
    } catch (error) {
        alert('Error saving settings: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Settings';
    }
});

// Setup Ollama
document.getElementById('setup-ollama-btn').addEventListener('click', async () => {
    const btn = document.getElementById('setup-ollama-btn');
    const detail = document.getElementById('ollama-status-detail');
    
    btn.disabled = true;
    btn.textContent = 'Setting up...';
    detail.className = 'status-detail';
    detail.textContent = 'Installing... This may take a few minutes.';
    
    try {
        const statusRes = await fetch('/api/ai/status');
        const status = await statusRes.json();
        
        if (!status.installed) {
            const installRes = await fetch('/api/ai/install-ollama', {
                method: 'POST'
            });
            const result = await installRes.json();
            
            if (!result.success) {
                detail.className = 'status-detail error';
                detail.textContent = '✗ ' + result.message;
                btn.disabled = false;
                btn.textContent = 'Retry Setup';
                return;
            }
        }
        
        if (status.model_available === false) {
            detail.textContent = 'Downloading model... This may take several minutes.';
            const pullRes = await fetch('/api/ai/pull-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: currentConfig.ollama_model })
            });
            const result = await pullRes.json();
            
            if (!result.success) {
                detail.className = 'status-detail error';
                detail.textContent = '✗ ' + result.message;
                btn.disabled = false;
                btn.textContent = 'Retry Setup';
                return;
            }
        }
        
        detail.className = 'status-detail success';
        detail.textContent = '✓ Setup complete!';
        btn.style.display = 'none';
        await checkAIStatus();
    } catch (error) {
        detail.className = 'status-detail error';
        detail.textContent = '✗ Error: ' + error.message;
        btn.disabled = false;
        btn.textContent = 'Retry Setup';
    }
});

// Scan for hand histories
document.getElementById('scan-btn').addEventListener('click', async () => {
    const btn = document.getElementById('scan-btn');
    const results = document.getElementById('scan-results');
    
    btn.disabled = true;
    btn.textContent = 'Scanning...';
    results.className = 'results info show';
    results.innerHTML = '<div class="loading"><div class="spinner"></div>Scanning for hand histories...</div>';
    
    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            handsFound = data.hands_found;
            results.className = 'results success show';
            results.innerHTML = `
                <strong>✓ Scan Complete</strong><br>
                Found ${data.files_found} file(s) with ${data.hands_found} hands for your player<br>
                ${data.hands.length > 0 ? '<br>Recent hands: ' + data.hands.slice(0, 5).map(h => 
                    `Hand #${h.hand_id} (${h.cards}) - ${h.result}`
                ).join('<br>') : ''}
            `;
            document.getElementById('analyze-btn').disabled = false;
        } else {
            results.className = 'results error show';
            results.innerHTML = `<strong>✗ Error:</strong> ${data.error}`;
        }
    } catch (error) {
        results.className = 'results error show';
        results.innerHTML = `<strong>✗ Error:</strong> ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Scan for Hand Histories';
    }
});

// Analyze hands
document.getElementById('analyze-btn').addEventListener('click', async () => {
    const btn = document.getElementById('analyze-btn');
    const results = document.getElementById('analyze-results');
    const container = document.getElementById('analyses-container');
    const limit = parseInt(document.getElementById('hand-limit').value);
    
    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    results.className = 'results info show';
    results.innerHTML = '<div class="loading"><div class="spinner"></div>Analyzing hands with AI... This may take a minute...</div>';
    container.innerHTML = '';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit })
        });
        
        const data = await response.json();
        
        if (data.success) {
            results.className = 'results success show';
            results.innerHTML = `
                <strong>✓ Analysis Complete</strong><br>
                Analyzed ${data.analyzed} of ${data.total_hands} total hands
            `;
            
            // Display analyses
            data.analyses.forEach(analysis => {
                const card = document.createElement('div');
                card.className = 'analysis-card';
                card.innerHTML = `
                    <div class="analysis-header">
                        <h3>Hand #${analysis.hand_id}</h3>
                        <div class="hand-info">
                            Cards: ${analysis.cards} | Result: ${analysis.result}
                        </div>
                    </div>
                    <div class="analysis-content">${analysis.analysis}</div>
                `;
                container.appendChild(card);
            });
        } else {
            results.className = 'results error show';
            results.innerHTML = `<strong>✗ Error:</strong> ${data.error}`;
        }
    } catch (error) {
        results.className = 'results error show';
        results.innerHTML = `<strong>✗ Error:</strong> ${error.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Hands';
    }
});

// Load status on page load
loadStatus();
