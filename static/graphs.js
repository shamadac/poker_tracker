// Graphs Page JavaScript
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
            
            // Create all charts
            createWinRateChart();
            createVPIPPFRChart();
            createPositionChart();
            createResultsChart();
            createAggressionChart();
            createDailyChart();
            
            // Show graphs
            loadingScreen.style.display = 'none';
            graphsContent.style.display = 'block';
        } else {
            loadingScreen.innerHTML = `
                <div class="error-message">
                    <h3>❌ Error Loading Data</h3>
                    <p>${data.error}</p>
                    <p>Please scan for hands first on the main page.</p>
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
            
            if (timeFilter === 'today' && daysDiff > 1) return false;
            if (timeFilter === 'week' && daysDiff > 7) return false;
            if (timeFilter === 'month' && daysDiff > 30) return false;
        }
        
        return true;
    });
    
    // Update info
    document.getElementById('filter-info').textContent = 
        `Showing ${filteredHands.length} of ${allHands.length} hands`;
    
    // Update all charts
    updateAllCharts();
}

// Create Win Rate Over Time Chart
function createWinRateChart() {
    const ctx = document.getElementById('winRateChart');
    
    // Calculate cumulative win rate
    const data = [];
    let wins = 0;
    let total = 0;
    
    filteredHands.forEach((hand, index) => {
        total++;
        if (hand.won) wins++;
        
        // Sample every 5 hands to keep chart readable
        if (index % 5 === 0 || index === filteredHands.length - 1) {
            data.push({
                x: total,
                y: (wins / total * 100).toFixed(1)
            });
        }
    });
    
    charts.winRate = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Win Rate %',
                data: data,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
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
                        text: 'Hands Played'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

// Create VPIP & PFR Trend Chart
function createVPIPPFRChart() {
    const ctx = document.getElementById('vpipPfrChart');
    
    // Calculate rolling VPIP/PFR (every 10 hands)
    const vpipData = [];
    const pfrData = [];
    const windowSize = 10;
    
    for (let i = windowSize; i <= filteredHands.length; i += 5) {
        const window = filteredHands.slice(Math.max(0, i - windowSize), i);
        
        // Simple VPIP calculation (hands with actions)
        const vpip = (window.filter(h => h.actions > 0).length / window.length * 100).toFixed(1);
        
        // Estimate PFR (this is simplified)
        const pfr = (window.filter(h => h.actions > 1).length / window.length * 100).toFixed(1);
        
        vpipData.push({ x: i, y: vpip });
        pfrData.push({ x: i, y: pfr });
    }
    
    charts.vpipPfr = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'VPIP (How often you play)',
                    data: vpipData,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'PFR (How often you raise)',
                    data: pfrData,
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Hands Played'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Percentage %'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

// Create Position Performance Chart
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
    
    const labels = Object.keys(positions);
    const winRates = labels.map(pos => 
        (positions[pos].wins / positions[pos].total * 100).toFixed(1)
    );
    const handCounts = labels.map(pos => positions[pos].total);
    
    charts.position = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Win Rate %',
                    data: winRates,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Hands Played',
                    data: handCounts,
                    backgroundColor: 'rgba(153, 102, 255, 0.6)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    min: 0,
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Hands Played'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Create Results Distribution Chart
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
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(108, 117, 125, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(108, 117, 125, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = wins + losses + folds;
                            const percentage = (context.parsed / total * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Create Aggression Chart
function createAggressionChart() {
    const ctx = document.getElementById('aggressionChart');
    
    // Calculate rolling aggression
    const data = [];
    const windowSize = 10;
    
    for (let i = windowSize; i <= filteredHands.length; i += 5) {
        const window = filteredHands.slice(Math.max(0, i - windowSize), i);
        
        // Simplified aggression: more actions = more aggressive
        const avgActions = window.reduce((sum, h) => sum + h.actions, 0) / window.length;
        
        data.push({ x: i, y: avgActions.toFixed(2) });
    }
    
    charts.aggression = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Aggression Level',
                data: data,
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Hands Played'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Avg Actions per Hand'
                    },
                    min: 0
                }
            }
        }
    });
}

// Create Daily Performance Chart
function createDailyChart() {
    const ctx = document.getElementById('dailyChart');
    
    // Group by date
    const dailyData = {};
    filteredHands.forEach(hand => {
        const date = hand.date.split(' ')[0]; // Get just the date part
        if (!dailyData[date]) {
            dailyData[date] = { total: 0, wins: 0 };
        }
        dailyData[date].total++;
        if (hand.won) dailyData[date].wins++;
    });
    
    const dates = Object.keys(dailyData).sort();
    const winRates = dates.map(date => 
        (dailyData[date].wins / dailyData[date].total * 100).toFixed(1)
    );
    
    charts.daily = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Daily Win Rate %',
                data: winRates,
                backgroundColor: winRates.map(rate => 
                    rate >= 50 ? 'rgba(40, 167, 69, 0.6)' : 'rgba(220, 53, 69, 0.6)'
                ),
                borderColor: winRates.map(rate => 
                    rate >= 50 ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)'
                ),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    min: 0,
                    max: 100
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
    
    // Recreate all charts with filtered data
    createWinRateChart();
    createVPIPPFRChart();
    createPositionChart();
    createResultsChart();
    createAggressionChart();
    createDailyChart();
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
