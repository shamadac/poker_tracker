// Dashboard JavaScript
let allHands = [];
let filteredHands = [];

// Load dashboard data on page load
async function loadDashboard() {
    const loadingScreen = document.getElementById('loading-screen');
    const dashboardContent = document.getElementById('dashboard-content');
    
    try {
        const response = await fetch('/api/dashboard/data');
        const data = await response.json();
        
        if (data.success) {
            allHands = data.hands;
            filteredHands = [...allHands];
            
            // Add money type breakdown if available
            if (data.play_money_count !== undefined && data.real_money_count !== undefined) {
                const headerH1 = document.querySelector('.dashboard-header h1');
                if (headerH1 && !document.getElementById('money-breakdown')) {
                    const breakdown = document.createElement('div');
                    breakdown.id = 'money-breakdown';
                    breakdown.style.fontSize = '0.5em';
                    breakdown.style.color = '#666';
                    breakdown.style.fontWeight = 'normal';
                    breakdown.style.marginTop = '5px';
                    breakdown.innerHTML = `
                        <span style="color: #667eea;">●</span> ${data.play_money_count} Play Money 
                        <span style="margin: 0 10px;">|</span>
                        <span style="color: #f5576c;">●</span> ${data.real_money_count} Real Money
                    `;
                    headerH1.appendChild(breakdown);
                }
            }
            
            // Update overview stats
            updateOverviewStats(data.stats, data.total_hands);
            
            // Update performance chart
            updatePerformanceChart(data.stats);
            
            // Populate hands table
            populateHandsTable(filteredHands);
            
            // Show dashboard
            loadingScreen.style.display = 'none';
            dashboardContent.style.display = 'block';
        } else {
            loadingScreen.innerHTML = `
                <div class="error-message">
                    <h3>❌ Error Loading Data</h3>
                    <p>${data.error}</p>
                    <a href="/" class="btn btn-primary">Go to Main Page</a>
                </div>
            `;
        }
    } catch (error) {
        loadingScreen.innerHTML = `
            <div class="error-message">
                <h3>❌ Error</h3>
                <p>${error.message}</p>
                <a href="/" class="btn btn-primary">Go to Main Page</a>
            </div>
        `;
    }
}

// Update overview statistics
function updateOverviewStats(stats, totalHands) {
    const winRate = stats.win_rate || {};
    
    document.getElementById('total-hands').textContent = totalHands;
    document.getElementById('win-rate').textContent = winRate.win_percentage + '%';
    document.getElementById('vpip').textContent = stats.vpip + '%';
    document.getElementById('pfr').textContent = stats.pfr + '%';
    document.getElementById('aggression').textContent = stats.aggression;
    document.getElementById('hands-won').textContent = winRate.wins || 0;
}

// Update performance chart
function updatePerformanceChart(stats) {
    const winRate = stats.win_rate || {};
    const total = (winRate.wins || 0) + (winRate.losses || 0) + (winRate.folds || 0);
    
    if (total === 0) return;
    
    const winsPercent = ((winRate.wins || 0) / total) * 100;
    const lossesPercent = ((winRate.losses || 0) / total) * 100;
    const foldsPercent = ((winRate.folds || 0) / total) * 100;
    
    // Animate bars
    setTimeout(() => {
        document.getElementById('wins-bar').style.width = winsPercent + '%';
        document.getElementById('losses-bar').style.width = lossesPercent + '%';
        document.getElementById('folds-bar').style.width = foldsPercent + '%';
    }, 100);
    
    document.getElementById('wins-count').textContent = winRate.wins || 0;
    document.getElementById('losses-count').textContent = winRate.losses || 0;
    document.getElementById('folds-count').textContent = winRate.folds || 0;
}

// Populate hands table
function populateHandsTable(hands) {
    const tbody = document.getElementById('hands-table-body');
    tbody.innerHTML = '';
    
    if (hands.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px; color: #999;">
                    No hands found matching your filters
                </td>
            </tr>
        `;
        document.getElementById('table-info').textContent = 'Showing 0 hands';
        return;
    }
    
    hands.forEach(hand => {
        const row = document.createElement('tr');
        
        // Determine result type
        let resultClass = '';
        let resultBadge = '';
        if (hand.result.toLowerCase().includes('won')) {
            resultClass = 'win-row';
            resultBadge = '<span class="result-badge won">Won</span>';
        } else if (hand.result.toLowerCase().includes('lost')) {
            resultClass = 'loss-row';
            resultBadge = '<span class="result-badge lost">Lost</span>';
        } else if (hand.result.toLowerCase().includes('fold')) {
            resultClass = '';
            resultBadge = '<span class="result-badge folded">Folded</span>';
        } else {
            resultBadge = '<span class="result-badge">' + hand.result + '</span>';
        }
        
        // Money type badge
        const moneyTypeBadge = hand.is_play_money 
            ? '<span class="money-badge play-money">Play Money</span>'
            : '<span class="money-badge real-money">Real Money</span>';
        
        row.className = resultClass;
        row.innerHTML = `
            <td class="hand-id-cell">${hand.hand_id}</td>
            <td>${formatDate(hand.date)}</td>
            <td>${moneyTypeBadge}</td>
            <td>${hand.game_type}</td>
            <td>${hand.stakes}</td>
            <td class="cards-cell">${formatCards(hand.player_cards)}</td>
            <td><span class="position-badge">${hand.position}</span></td>
            <td>${resultBadge}</td>
            <td>${hand.pot_size}</td>
            <td>${hand.actions}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    document.getElementById('table-info').textContent = `Showing ${hands.length} hand${hands.length !== 1 ? 's' : ''}`;
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    // Simple date formatting - can be enhanced
    return dateStr.split(' ')[0] || dateStr;
}

// Format cards with suit symbols
function formatCards(cards) {
    if (!cards || cards === 'unknown') return 'N/A';
    
    // Add color styling for suits
    let formatted = cards
        .replace(/([AKQJT98765432]+)s/g, '<span style="color: #000;">$1♠</span>')
        .replace(/([AKQJT98765432]+)h/g, '<span style="color: #e74c3c;">$1♥</span>')
        .replace(/([AKQJT98765432]+)d/g, '<span style="color: #3498db;">$1♦</span>')
        .replace(/([AKQJT98765432]+)c/g, '<span style="color: #27ae60;">$1♣</span>');
    
    return formatted;
}

// Search functionality
document.getElementById('search-input').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    applyFilters(searchTerm);
});

// Filter functionality
document.getElementById('filter-result').addEventListener('change', (e) => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    applyFilters(searchTerm);
});

// Money type filter
document.getElementById('filter-money-type').addEventListener('change', (e) => {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    applyFilters(searchTerm);
});

// Apply filters
function applyFilters(searchTerm = '') {
    const resultFilter = document.getElementById('filter-result').value;
    const moneyTypeFilter = document.getElementById('filter-money-type').value;
    
    filteredHands = allHands.filter(hand => {
        // Apply money type filter
        if (moneyTypeFilter === 'real' && hand.is_play_money) {
            return false;
        }
        if (moneyTypeFilter === 'play' && !hand.is_play_money) {
            return false;
        }
        
        // Apply result filter
        if (resultFilter !== 'all') {
            if (!hand.result.toLowerCase().includes(resultFilter)) {
                return false;
            }
        }
        
        // Apply search filter
        if (searchTerm) {
            const searchableText = `
                ${hand.hand_id}
                ${hand.game_type}
                ${hand.stakes}
                ${hand.player_cards}
                ${hand.position}
                ${hand.result}
            `.toLowerCase();
            
            if (!searchableText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    populateHandsTable(filteredHands);
}

// Refresh button
document.getElementById('refresh-btn').addEventListener('click', async () => {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.textContent = '🔄 Refreshing...';
    
    // Clear cache and reload
    await fetch('/api/scan', { method: 'POST' });
    await loadDashboard();
    
    btn.disabled = false;
    btn.textContent = '🔄 Refresh Data';
});

// Load dashboard on page load
loadDashboard();
