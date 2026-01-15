// Graphs Page JavaScript - Professional & Beginner-Friendly
let allHands = [];
let filteredHands = [];
let charts = {};

// Load graphs data
async function loadGraphs() {
    const loadingScreen = document.getElementById('loading-screen');
    const graphsContent = document.getElementById('graphs-content');
    
    try {
        const response = await fetch('/api/dashboard/data');
        const data = await response.json();
        
        if (data.success) {
            allHands = data.hands;
            filteredHands = [...allHands];
            
            // Populate stakes filter
            populateStakesFilter();
            
            // Update metrics and create charts
            updateMetrics();
            createWinRateChart();
            createResultsChart();
            createPositionChart();
            
            // Show graphs
            loadingScreen.style.display = 'none';
            graphsContent.style.display = 'block';
        } else {
            loadingScreen.innerHTML = `
                <div class="error-message">
                    <h3>No Data Available</h3>
                    <p>Please scan for hands first on the main page.</p>
                    <a href="/" class="btn btn-primary">Go to Main Page</a>
                </div>
            `;
        }
    } catch (error) {
        loadingScreen.innerHTML = `
            <div class="error-message">
                <h3>Error Loading Data</h3>
                <p>${error.message}</p>
                <a href="/" class="btn btn-primary">Go to Main Page</a>
            </div>
        `;
    }
}

// Populate stakes filter
function populateStakesFilter() {
    const stakesSet = new Set();
    allHands.forEach(hand => {
        if (hand.stakes && hand.stakes !== 'unknown') {
            stakesSet.add(hand.stakes);
        }
    });
    
    const select = document.getElementById('filter-stakes');
    stakesSet.forEach(stakes => {
        const option = document.createElement('option');
        option.value = stakes;
        option.textContent = stakes;
        select.appendChild(option);
    });
}

// Update key metrics
function updateMetrics() {
    const totalHands = filteredHands.length;
    const wins = filteredHands.filter(h => h.won).length;
    const winRate = totalHands > 0 ? ((wins / totalHands) * 100).toFixed(1) : 0;
    
    // Calculate VPIP (hands where player put money in voluntarily)
    const vpipHands = filteredHands.filter(h => h.actions > 0).length;
    const vpip = totalHands > 0 ? ((vpipHands / totalHands) * 100).toFixed(1) : 0;
    
    // Find best position
    const positions = {};
    filteredHands.forEach(hand => {
        const pos = hand.position || 'Unknown';
        if (!positions[pos]) {
            positions[pos] = { total: 0, wins: 0 };
        }
        positions[pos].total++;
        if (hand.won) positions[pos].wins++;
    });
    
    let bestPosition = '-';
    let bestWinRate = 0;
    Object.keys(positions).forEach(pos => {
        const rate = positions[pos].wins / positions[pos].total;
        if (rate > bestWinRate && positions[pos].total >= 3) {
            bestWinRate = rate;
            bestPosition = pos;
        }
    });
    
    // Update DOM
    document.getElementById('metric-winrate').textContent = `${winRate}%`;
    document.getElementById('metric-hands').textContent = totalHands;
    document.getElementById('metric-vpip').textContent = `${vpip}%`;
    document.getElementById('metric-position').textContent = bestPosition;
}

// Apply filters
function applyFilters() {
    const gameType = document.getElementById('filter-game-type').value;
    const timeFilter = document.getElementById('filter-time').value;
    const stakes = document.getElementById('filter-stakes').value;
    
    filteredHands = allHands.filter(hand => {
        // Game type filter
        if (gameType === 'real' && hand.is_play_money) return false;
        if (gameType === 'play' && !hand.is_play_money) return false;
        
        // Stakes filter
        if (stakes !== 'all' && hand.stakes !== stakes) return false;
        
        // Time filter
        if (timeFilter !== 'all') {
            const handDate = new Date(hand.date);
            const now = new Date();
            const daysDiff = (now - handDate) / (1000 * 60 * 60 * 24);
            
            if (timeFilter === 'week' && daysDiff > 7) return false;
            if (timeFilter === 'month' && daysDiff > 30) return false;
        }
        
        return true;
    });
    
    // Update info
    document.getElementById('filter-info').textContent = 
        `Showing ${filteredHands.length} of ${allHands.length} hands`;
    
    // Update all charts and metrics
    updateAllCharts();
}

// Create Win Rate Chart
function createWinRateChart() {
    const ctx = document.getElementById('winRateChart');
    
    // Calculate cumulative win rate
    const data = [];
    let wins = 0;
    let total = 0;
    
    filteredHands.forEach((hand, index) => {
        total++;
        if (hand.won) wins++;
        
        // Add data point every 3 hands or at the end
        if (total % 3 === 0 || index === filteredHands.length - 1) {
            data.push({
                x: total,
                y: parseFloat((wins / total * 100).toFixed(1))
            });
        }
    });
    
    charts.winRate = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Win Rate',
                data: data,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        title: function(context) {
                            return `Hand ${context[0].parsed.x}`;
                        },
                        label: function(context) {
                            return `Win Rate: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Hands Played',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Win Rate (%)',
                        font: { size: 12, weight: '600' }
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Create Results Chart
function createResultsChart() {
    const ctx = document.getElementById('resultsChart');
    
    const wins = filteredHands.filter(h => h.result.toLowerCase().includes('won')).length;
    const losses = filteredHands.filter(h => h.result.toLowerCase().includes('lost')).length;
    const folds = filteredHands.filter(h => h.result.toLowerCase().includes('fold')).length;
    
    charts.results = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Wins', 'Losses', 'Folds'],
            datasets: [{
                data: [wins, losses, folds],
                backgroundColor: [
                    '#10b981',
                    '#ef4444',
                    '#9ca3af'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12, weight: '500' },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            const total = wins + losses + folds;
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Create Position Chart
function createPositionChart() {
    const ctx = document.getElementById('positionChart');
    
    // Group by position
    const positions = {};
    filteredHands.forEach(hand => {
        const pos = hand.position || 'Unknown';
        if (!positions[pos]) {
            positions[pos] = { total: 0, wins: 0 };
        }
        positions[pos].total++;
        if (hand.won) positions[pos].wins++;
    });
    
    // Sort positions by standard poker order
    const positionOrder = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN', 'Unknown'];
    const labels = Object.keys(positions).sort((a, b) => {
        const aIndex = positionOrder.indexOf(a);
        const bIndex = positionOrder.indexOf(b);
        return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex);
    });
    
    const winRates = labels.map(pos => 
        parseFloat((positions[pos].wins / positions[pos].total * 100).toFixed(1))
    );
    
    charts.position = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Win Rate',
                data: winRates,
                backgroundColor: winRates.map(rate => 
                    rate >= 50 ? '#10b981' : '#2563eb'
                ),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            const pos = context.label;
                            const hands = positions[pos].total;
                            return [
                                `Win Rate: ${context.parsed.y}%`,
                                `Hands: ${hands}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 11, weight: '600' }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Win Rate (%)',
                        font: { size: 12, weight: '600' }
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update all charts
function updateAllCharts() {
    // Destroy existing charts
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    // Update metrics
    updateMetrics();
    
    // Recreate all charts with filtered data
    createWinRateChart();
    createResultsChart();
    createPositionChart();
}

// Filter event listeners
document.getElementById('filter-game-type').addEventListener('change', applyFilters);
document.getElementById('filter-time').addEventListener('change', applyFilters);
document.getElementById('filter-stakes').addEventListener('change', applyFilters);

// Refresh button
document.getElementById('refresh-graphs-btn').addEventListener('click', async () => {
    const btn = document.getElementById('refresh-graphs-btn');
    btn.disabled = true;
    btn.textContent = '🔄 Refreshing...';
    
    await fetch('/api/scan', { method: 'POST' });
    location.reload();
});

// Load graphs on page load
loadGraphs();
