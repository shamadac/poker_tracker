// Main application JavaScript
let handsFound = 0;

// Load initial config and status
async function loadStatus() {
    try {
        const configRes = await fetch('/api/config');
        const config = await configRes.json();
        document.getElementById('player-name').textContent = config.username;

        const statusRes = await fetch('/api/status');
        const status = await statusRes.json();
        const ollamaStatus = document.getElementById('ollama-status');
        
        if (status.ollama_connected) {
            ollamaStatus.textContent = '✓ Connected';
            ollamaStatus.style.color = '#28a745';
        } else {
            ollamaStatus.textContent = '✗ Not Connected';
            ollamaStatus.style.color = '#dc3545';
        }
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

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
    const playstyleContainer = document.getElementById('playstyle-container');
    const limit = parseInt(document.getElementById('hand-limit').value);
    
    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    results.className = 'results info show';
    results.innerHTML = '<div class="loading"><div class="spinner"></div>Analyzing hands with AI... This may take a few minutes...</div>';
    container.innerHTML = '';
    playstyleContainer.innerHTML = '';
    
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
            
            // Display playstyle report first
            if (data.playstyle_report && data.overall_recommendations) {
                playstyleContainer.innerHTML = renderPlaystyleReport(
                    data.playstyle_report, 
                    data.overall_recommendations
                );
            }
            
            // Display individual hand analyses
            data.analyses.forEach((analysis, index) => {
                const card = document.createElement('div');
                card.className = 'analysis-card';
                card.innerHTML = `
                    <div class="analysis-header">
                        <h3>Hand #${analysis.hand_id}</h3>
                        <div class="hand-info">
                            Result: ${analysis.result}
                        </div>
                    </div>
                    <div class="player-cards-section">
                        <strong>Your Cards:</strong> ${renderCards(analysis.cards)}
                    </div>
                    <div class="analysis-content">${analysis.analysis}</div>
                    <button class="expand-btn" onclick="toggleHandDetails(${index})">
                        Show Full Hand History
                    </button>
                    <div id="hand-details-${index}" class="hand-details">
                        ${renderHandDetails(analysis.hand_details)}
                    </div>
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
        btn.textContent = 'Analyze Hands & Generate Report';
    }
});

// Toggle hand details
function toggleHandDetails(index) {
    const details = document.getElementById(`hand-details-${index}`);
    const btn = event.target;
    
    if (details.classList.contains('show')) {
        details.classList.remove('show');
        btn.textContent = 'Show Full Hand History';
    } else {
        details.classList.add('show');
        btn.textContent = 'Hide Full Hand History';
    }
}

// Make function global
window.toggleHandDetails = toggleHandDetails;

// Load status on page load
loadStatus();
