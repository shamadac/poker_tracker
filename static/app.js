// Main application JavaScript
let handsFound = 0;
let progressInterval = null;

// Theme Toggle
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        updateThemeIcon(true);
    }
}

function updateThemeIcon(isDark) {
    const icon = document.querySelector('.theme-icon');
    icon.textContent = isDark ? '☀️' : '🌙';
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    
    const themeToggle = document.getElementById('theme-toggle');
    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeIcon(isDark);
    });
});

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
                Found ${data.files_found} file(s) with ${data.hands_found} hands for your player
            `;
            document.getElementById('analyze-summary-btn').disabled = false;
            document.getElementById('analyze-detailed-btn').disabled = false;
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

// Analyze summary only (all hands)
document.getElementById('analyze-summary-btn').addEventListener('click', async () => {
    await runAnalysis(true, false);
});

// Analyze with individual hands
document.getElementById('analyze-detailed-btn').addEventListener('click', async () => {
    await runAnalysis(false, true);
});

// Main analysis function
async function runAnalysis(analyzeAll, includeIndividual) {
    const summaryBtn = document.getElementById('analyze-summary-btn');
    const detailedBtn = document.getElementById('analyze-detailed-btn');
    const results = document.getElementById('analyze-results');
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const summaryContainer = document.getElementById('summary-container');
    const statsContainer = document.getElementById('stats-container');
    const playstyleContainer = document.getElementById('playstyle-container');
    const analysesContainer = document.getElementById('analyses-container');
    
    // Disable buttons
    summaryBtn.disabled = true;
    detailedBtn.disabled = true;
    
    // Show progress
    progressContainer.style.display = 'block';
    progressFill.style.width = '10%';
    progressText.textContent = 'Starting analysis...';
    
    // Clear previous results
    results.className = 'results info show';
    results.innerHTML = '';
    summaryContainer.innerHTML = '';
    statsContainer.innerHTML = '';
    playstyleContainer.innerHTML = '';
    analysesContainer.innerHTML = '';
    
    // Simulate progress (since we don't have real-time updates yet)
    let progress = 10;
    progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += 5;
            progressFill.style.width = progress + '%';
            if (progress < 30) {
                progressText.textContent = 'Analyzing hand histories...';
            } else if (progress < 60) {
                progressText.textContent = 'Calculating statistics...';
            } else {
                progressText.textContent = 'Generating AI insights...';
            }
        }
    }, 1000);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                analyze_all: analyzeAll,
                include_individual: includeIndividual
            })
        });
        
        const data = await response.json();
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressText.textContent = 'Complete!';
        
        if (data.success) {
            results.className = 'results success show';
            results.innerHTML = `
                <strong>✓ Analysis Complete</strong><br>
                Analyzed ${data.total_hands} hands
            `;
            
            // Display statistics with visualizations
            if (data.playstyle_report) {
                statsContainer.innerHTML = renderStatistics(data.playstyle_report, data.total_hands);
            }
            
            // Display executive summary
            if (data.overall_recommendations) {
                summaryContainer.innerHTML = renderExecutiveSummary(data.overall_recommendations);
            }
            
            // Display individual hand analyses if requested
            if (includeIndividual && data.analyses && data.analyses.length > 0) {
                analysesContainer.innerHTML = '<div class="section-header"><h2>📋 Individual Hand Analysis</h2></div>';
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
                    analysesContainer.appendChild(card);
                });
            }
            
            // Hide progress after a delay
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 2000);
        } else {
            results.className = 'results error show';
            results.innerHTML = `<strong>✗ Error:</strong> ${data.error}`;
            progressContainer.style.display = 'none';
        }
    } catch (error) {
        clearInterval(progressInterval);
        results.className = 'results error show';
        results.innerHTML = `<strong>✗ Error:</strong> ${error.message}`;
        progressContainer.style.display = 'none';
    } finally {
        summaryBtn.disabled = false;
        detailedBtn.disabled = false;
    }
}

// Render executive summary
function renderExecutiveSummary(analysis) {
    // Convert markdown-style formatting to HTML with better structure
    let formatted = analysis
        .replace(/## (.*)/g, '<h2 class="summary-heading">$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/(\d+)\.\s+([^\n]+)/g, '<div class="summary-item"><span class="item-number">$1</span><span class="item-text">$2</span></div>')
        .replace(/\n\n/g, '</p><p>');
    
    return `
        <div class="executive-summary">
            <div class="section-header">
                <h2>📊 Your Poker Analysis</h2>
                <p class="subtitle">Beginner-friendly insights to improve your game</p>
            </div>
            <div class="summary-content">
                ${formatted}
            </div>
        </div>
    `;
}

// Render statistics with visualizations
function renderStatistics(stats, totalHands) {
    const winRate = stats.win_rate || {};
    
    return `
        <div class="statistics-panel">
            <div class="section-header">
                <h2>📈 Your Statistics</h2>
                <p class="subtitle">Based on ${totalHands} hands</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">VPIP</div>
                    <div class="stat-value">${stats.vpip}%</div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${Math.min(stats.vpip, 100)}%; background: #4CAF50;"></div>
                    </div>
                    <div class="stat-description">Voluntarily Put $ In Pot</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">PFR</div>
                    <div class="stat-value">${stats.pfr}%</div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${Math.min(stats.pfr, 100)}%; background: #2196F3;"></div>
                    </div>
                    <div class="stat-description">Pre-Flop Raise</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Aggression</div>
                    <div class="stat-value">${stats.aggression}</div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${Math.min(stats.aggression * 20, 100)}%; background: #FF9800;"></div>
                    </div>
                    <div class="stat-description">Aggression Factor</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value">${winRate.win_percentage}%</div>
                    <div class="stat-bar">
                        <div class="stat-bar-fill" style="width: ${winRate.win_percentage}%; background: #9C27B0;"></div>
                    </div>
                    <div class="stat-description">${winRate.wins}W / ${winRate.losses}L / ${winRate.folds}F</div>
                </div>
            </div>
            
            <div class="win-loss-chart">
                <h3>Hand Outcomes</h3>
                <div class="chart-container">
                    <div class="chart-bar wins" style="width: ${(winRate.wins / totalHands) * 100}%">
                        <span class="chart-label">Wins: ${winRate.wins}</span>
                    </div>
                    <div class="chart-bar losses" style="width: ${(winRate.losses / totalHands) * 100}%">
                        <span class="chart-label">Losses: ${winRate.losses}</span>
                    </div>
                    <div class="chart-bar folds" style="width: ${(winRate.folds / totalHands) * 100}%">
                        <span class="chart-label">Folds: ${winRate.folds}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

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
