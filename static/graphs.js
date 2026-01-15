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
            createProfitChart();
            createHandStrengthChart();
            createAggressionChart();
            createSessionChart();
            createBankrollChart();
            createStartingHandsChart();
            createHandRangeHeatmap();
            createStreakChart();
            createRadarChart();
            
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

// Create Profit/Loss Chart
function createProfitChart() {
    const ctx = document.getElementById('profitChart');
    
    // Calculate cumulative profit
    const data = [];
    let cumulativeProfit = 0;
    
    filteredHands.forEach((hand, index) => {
        // Estimate profit based on result
        let profit = 0;
        if (hand.result.toLowerCase().includes('won')) {
            // Extract amount from result if possible
            const match = hand.result.match(/[\d.]+/);
            profit = match ? parseFloat(match[0]) : 1;
        } else if (hand.result.toLowerCase().includes('lost')) {
            const match = hand.result.match(/[\d.]+/);
            profit = match ? -parseFloat(match[0]) : -0.5;
        }
        
        cumulativeProfit += profit;
        
        // Add data point every hand
        data.push({
            x: index + 1,
            y: parseFloat(cumulativeProfit.toFixed(2))
        });
    });
    
    charts.profit = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Cumulative Profit',
                data: data,
                borderColor: '#2563eb',
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return null;
                    
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.05)');
                    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.2)');
                    return gradient;
                },
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 2,
                pointHoverRadius: 6,
                pointBackgroundColor: function(context) {
                    return context.parsed.y >= 0 ? '#10b981' : '#ef4444';
                }
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
                            const value = context.parsed.y;
                            const sign = value >= 0 ? '+' : '';
                            return `Profit: ${sign}${value.toFixed(2)}`;
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
                        text: 'Cumulative Profit',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value >= 0 ? '+' + value : value;
                        }
                    }
                }
            }
        }
    });
}

// Create Hand Strength Chart
function createHandStrengthChart() {
    const ctx = document.getElementById('handStrengthChart');
    
    // Categorize hands by strength
    const categories = {
        'Premium (AA-QQ, AK)': 0,
        'Strong (JJ-99, AQ-AJ)': 0,
        'Medium (88-22, KQ-KJ)': 0,
        'Speculative (Suited, Connectors)': 0,
        'Weak (Others)': 0
    };
    
    filteredHands.forEach(hand => {
        if (!hand.hole_cards || hand.hole_cards === 'unknown') {
            categories['Weak (Others)']++;
            return;
        }
        
        const cards = hand.hole_cards.toUpperCase();
        
        // Premium hands
        if (cards.includes('AA') || cards.includes('KK') || cards.includes('QQ') || 
            (cards.includes('A') && cards.includes('K'))) {
            categories['Premium (AA-QQ, AK)']++;
        }
        // Strong hands
        else if (cards.includes('JJ') || cards.includes('TT') || cards.includes('99') ||
                 (cards.includes('A') && (cards.includes('Q') || cards.includes('J')))) {
            categories['Strong (JJ-99, AQ-AJ)']++;
        }
        // Medium pairs and broadway
        else if (/[2-8][2-8]/.test(cards) || 
                 (cards.includes('K') && (cards.includes('Q') || cards.includes('J')))) {
            categories['Medium (88-22, KQ-KJ)']++;
        }
        // Suited or connectors
        else if (cards.includes('s') || /[0-9][0-9]/.test(cards)) {
            categories['Speculative (Suited, Connectors)']++;
        }
        else {
            categories['Weak (Others)']++;
        }
    });
    
    const labels = Object.keys(categories);
    const data = Object.values(categories);
    
    charts.handStrength = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#10b981', // Premium - green
                    '#2563eb', // Strong - blue
                    '#f59e0b', // Medium - amber
                    '#8b5cf6', // Speculative - purple
                    '#9ca3af'  // Weak - gray
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
                        padding: 12,
                        font: { size: 11, weight: '500' },
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
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} hands (${percentage}%)`;
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
    
    // Count aggressive vs passive actions
    const actions = {
        'Aggressive (Bet/Raise)': 0,
        'Passive (Call/Check)': 0,
        'Fold': 0
    };
    
    filteredHands.forEach(hand => {
        const result = hand.result.toLowerCase();
        
        if (result.includes('bet') || result.includes('raise') || result.includes('all-in')) {
            actions['Aggressive (Bet/Raise)']++;
        } else if (result.includes('call') || result.includes('check')) {
            actions['Passive (Call/Check)']++;
        } else if (result.includes('fold')) {
            actions['Fold']++;
        } else {
            // Default categorization based on whether they won
            if (hand.won) {
                actions['Aggressive (Bet/Raise)']++;
            } else {
                actions['Passive (Call/Check)']++;
            }
        }
    });
    
    const labels = Object.keys(actions);
    const data = Object.values(actions);
    
    charts.aggression = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Actions',
                data: data,
                backgroundColor: [
                    '#ef4444', // Aggressive - red
                    '#2563eb', // Passive - blue
                    '#9ca3af'  // Fold - gray
                ],
                borderRadius: 8,
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
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${context.parsed.y} hands (${percentage}%)`;
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
                        text: 'Number of Hands',
                        font: { size: 12, weight: '600' }
                    },
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Create Session Performance Chart
function createSessionChart() {
    const ctx = document.getElementById('sessionChart');
    
    // Group hands by date (session)
    const sessions = {};
    filteredHands.forEach(hand => {
        const date = hand.date ? hand.date.split('T')[0] : 'Unknown';
        if (!sessions[date]) {
            sessions[date] = { wins: 0, total: 0, profit: 0 };
        }
        sessions[date].total++;
        if (hand.won) sessions[date].wins++;
        
        // Calculate profit
        if (hand.result.toLowerCase().includes('won')) {
            const match = hand.result.match(/[\d.]+/);
            sessions[date].profit += match ? parseFloat(match[0]) : 1;
        } else if (hand.result.toLowerCase().includes('lost')) {
            const match = hand.result.match(/[\d.]+/);
            sessions[date].profit -= match ? parseFloat(match[0]) : 0.5;
        }
    });
    
    const dates = Object.keys(sessions).sort();
    const winRates = dates.map(date => 
        parseFloat((sessions[date].wins / sessions[date].total * 100).toFixed(1))
    );
    const profits = dates.map(date => parseFloat(sessions[date].profit.toFixed(2)));
    
    charts.session = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates.map(d => {
                const date = new Date(d);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [
                {
                    label: 'Win Rate (%)',
                    data: winRates,
                    backgroundColor: 'rgba(16, 185, 129, 0.6)',
                    borderColor: '#10b981',
                    borderWidth: 2,
                    borderRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Profit',
                    data: profits,
                    type: 'line',
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15,
                        font: { size: 12, weight: '500' },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 }
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
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Win Rate (%)',
                        font: { size: 12, weight: '600' }
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
                        text: 'Profit',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Create Bankroll Growth Chart
function createBankrollChart() {
    const ctx = document.getElementById('bankrollChart');
    
    // Calculate bankroll over time
    const data = [];
    let bankroll = 100; // Starting bankroll
    
    filteredHands.forEach((hand, index) => {
        // Calculate profit/loss
        if (hand.result.toLowerCase().includes('won')) {
            const match = hand.result.match(/[\d.]+/);
            bankroll += match ? parseFloat(match[0]) : 1;
        } else if (hand.result.toLowerCase().includes('lost')) {
            const match = hand.result.match(/[\d.]+/);
            bankroll -= match ? parseFloat(match[0]) : 0.5;
        }
        
        data.push({
            x: index + 1,
            y: parseFloat(bankroll.toFixed(2))
        });
    });
    
    const startingBankroll = 100;
    const currentBankroll = data.length > 0 ? data[data.length - 1].y : startingBankroll;
    const profitLoss = currentBankroll - startingBankroll;
    const isProfit = profitLoss >= 0;
    
    charts.bankroll = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Bankroll',
                data: data,
                borderColor: isProfit ? '#10b981' : '#ef4444',
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return null;
                    
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    if (isProfit) {
                        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.05)');
                        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.3)');
                    } else {
                        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.05)');
                        gradient.addColorStop(1, 'rgba(239, 68, 68, 0.3)');
                    }
                    return gradient;
                },
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 2,
                pointHoverRadius: 6,
                pointBackgroundColor: isProfit ? '#10b981' : '#ef4444'
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
                            return `Bankroll: $${context.parsed.y.toFixed(2)}`;
                        },
                        afterLabel: function(context) {
                            const change = context.parsed.y - startingBankroll;
                            const sign = change >= 0 ? '+' : '';
                            return `Change: ${sign}$${change.toFixed(2)}`;
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
                        text: 'Bankroll ($)',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

// Create Starting Hands Chart
function createStartingHandsChart() {
    const ctx = document.getElementById('startingHandsChart');
    
    // Count starting hand categories
    const handCategories = {
        'Pocket Pairs': 0,
        'Suited Connectors': 0,
        'Broadway (High Cards)': 0,
        'Suited Aces': 0,
        'Offsuit High': 0,
        'Weak Hands': 0
    };
    
    filteredHands.forEach(hand => {
        if (!hand.hole_cards || hand.hole_cards === 'unknown') {
            handCategories['Weak Hands']++;
            return;
        }
        
        const cards = hand.hole_cards.toUpperCase();
        
        // Pocket pairs
        if (/([AKQJT98765432])\1/.test(cards.replace(/[shdc]/gi, ''))) {
            handCategories['Pocket Pairs']++;
        }
        // Suited Aces
        else if (cards.includes('A') && cards.includes('s')) {
            handCategories['Suited Aces']++;
        }
        // Suited connectors
        else if (cards.includes('s')) {
            handCategories['Suited Connectors']++;
        }
        // Broadway (high cards)
        else if (/[AKQJT].*[AKQJT]/.test(cards)) {
            handCategories['Broadway (High Cards)']++;
        }
        // Offsuit high
        else if (/[AKQJ]/.test(cards)) {
            handCategories['Offsuit High']++;
        }
        else {
            handCategories['Weak Hands']++;
        }
    });
    
    const labels = Object.keys(handCategories);
    const data = Object.values(handCategories);
    
    charts.startingHands = new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(16, 185, 129, 0.7)',   // Pocket Pairs - green
                    'rgba(139, 92, 246, 0.7)',   // Suited Connectors - purple
                    'rgba(37, 99, 235, 0.7)',    // Broadway - blue
                    'rgba(245, 158, 11, 0.7)',   // Suited Aces - amber
                    'rgba(59, 130, 246, 0.7)',   // Offsuit High - light blue
                    'rgba(156, 163, 175, 0.7)'   // Weak - gray
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        font: { size: 11, weight: '500' },
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
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed.r / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed.r} hands (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Create Hand Range Heatmap (PT4 Competitor Feature)
function createHandRangeHeatmap() {
    const container = document.getElementById('handRangeHeatmap');
    container.innerHTML = '';
    
    // Poker hand matrix (13x13 grid)
    const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
    
    // Count hands played
    const handCounts = {};
    const handWins = {};
    
    filteredHands.forEach(hand => {
        if (!hand.hole_cards || hand.hole_cards === 'unknown') return;
        
        const cards = hand.hole_cards.toUpperCase();
        // Normalize hand notation
        let handKey = cards.replace(/[shdc]/gi, '');
        
        if (!handCounts[handKey]) {
            handCounts[handKey] = 0;
            handWins[handKey] = 0;
        }
        handCounts[handKey]++;
        if (hand.won) handWins[handKey]++;
    });
    
    // Create grid
    ranks.forEach((rank1, i) => {
        ranks.forEach((rank2, j) => {
            const cell = document.createElement('div');
            cell.className = 'hand-cell';
            
            let handNotation = '';
            let handKey = '';
            
            if (i === j) {
                // Pocket pairs
                handNotation = rank1 + rank1;
                handKey = rank1 + rank1;
            } else if (i < j) {
                // Suited hands (upper right)
                handNotation = rank1 + rank2 + 's';
                handKey = rank1 + rank2;
            } else {
                // Offsuit hands (lower left)
                handNotation = rank2 + rank1 + 'o';
                handKey = rank2 + rank1;
            }
            
            const count = handCounts[handKey] || 0;
            const wins = handWins[handKey] || 0;
            const winRate = count > 0 ? (wins / count) : 0;
            
            // Color based on profitability
            let bgColor;
            if (count === 0) {
                bgColor = '#e5e7eb'; // Gray - not played
            } else if (winRate >= 0.6) {
                bgColor = '#10b981'; // Green - profitable
            } else if (winRate >= 0.4) {
                bgColor = '#f59e0b'; // Amber - break even
            } else {
                bgColor = '#ef4444'; // Red - losing
            }
            
            cell.style.backgroundColor = bgColor;
            cell.innerHTML = `
                <span class="hand-cell-label">${handNotation}</span>
                ${count > 0 ? `<span class="hand-cell-count">${count}</span>` : ''}
            `;
            
            cell.title = count > 0 
                ? `${handNotation}: ${count} hands, ${(winRate * 100).toFixed(0)}% win rate`
                : `${handNotation}: Not played`;
            
            container.appendChild(cell);
        });
    });
}

// Create Streak Chart (PT4 Competitor Feature)
function createStreakChart() {
    const ctx = document.getElementById('streakChart');
    
    // Calculate streaks
    const streaks = [];
    let currentStreak = 0;
    let streakType = null;
    
    filteredHands.forEach((hand, index) => {
        const won = hand.won;
        
        if (streakType === null) {
            streakType = won ? 'win' : 'loss';
            currentStreak = 1;
        } else if ((won && streakType === 'win') || (!won && streakType === 'loss')) {
            currentStreak++;
        } else {
            streaks.push({
                x: index,
                y: streakType === 'win' ? currentStreak : -currentStreak,
                type: streakType
            });
            streakType = won ? 'win' : 'loss';
            currentStreak = 1;
        }
    });
    
    // Add final streak
    if (currentStreak > 0) {
        streaks.push({
            x: filteredHands.length,
            y: streakType === 'win' ? currentStreak : -currentStreak,
            type: streakType
        });
    }
    
    charts.streak = new Chart(ctx, {
        type: 'bar',
        data: {
            datasets: [{
                label: 'Streaks',
                data: streaks,
                backgroundColor: function(context) {
                    return context.parsed.y > 0 ? '#10b981' : '#ef4444';
                },
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
                        title: function(context) {
                            return `Hand ${context[0].parsed.x}`;
                        },
                        label: function(context) {
                            const value = Math.abs(context.parsed.y);
                            const type = context.parsed.y > 0 ? 'Winning' : 'Losing';
                            return `${type} streak: ${value} hands`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Hand Number',
                        font: { size: 12, weight: '600' }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Streak Length',
                        font: { size: 12, weight: '600' }
                    },
                    ticks: {
                        callback: function(value) {
                            return Math.abs(value);
                        }
                    }
                }
            }
        }
    });
}

// Create Radar Chart (PT4 Competitor Feature)
function createRadarChart() {
    const ctx = document.getElementById('radarChart');
    
    // Calculate key metrics
    const totalHands = filteredHands.length;
    const wins = filteredHands.filter(h => h.won).length;
    const winRate = totalHands > 0 ? (wins / totalHands * 100) : 0;
    
    const vpipHands = filteredHands.filter(h => h.actions > 0).length;
    const vpip = totalHands > 0 ? (vpipHands / totalHands * 100) : 0;
    
    const aggressiveHands = filteredHands.filter(h => 
        h.result.toLowerCase().includes('bet') || 
        h.result.toLowerCase().includes('raise')
    ).length;
    const aggression = vpipHands > 0 ? (aggressiveHands / vpipHands * 100) : 0;
    
    // Position awareness (BTN/CO win rate vs blinds)
    const latePos = filteredHands.filter(h => h.position === 'BTN' || h.position === 'CO');
    const latePosWins = latePos.filter(h => h.won).length;
    const positionPlay = latePos.length > 0 ? (latePosWins / latePos.length * 100) : 50;
    
    // Fold discipline (fold rate)
    const folds = filteredHands.filter(h => h.result.toLowerCase().includes('fold')).length;
    const foldRate = totalHands > 0 ? (folds / totalHands * 100) : 0;
    const discipline = 100 - Math.min(foldRate, 80); // Inverse - higher is better
    
    // Optimal values for comparison
    const optimalValues = [55, 25, 60, 65, 70]; // Win Rate, VPIP, Aggression, Position, Discipline
    const yourValues = [winRate, vpip, aggression, positionPlay, discipline];
    
    charts.radar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Win Rate', 'VPIP', 'Aggression', 'Position Play', 'Discipline'],
            datasets: [
                {
                    label: 'Your Stats',
                    data: yourValues,
                    backgroundColor: 'rgba(37, 99, 235, 0.2)',
                    borderColor: '#2563eb',
                    borderWidth: 3,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#2563eb',
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: 'Optimal Play',
                    data: optimalValues,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderColor: '#10b981',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15,
                        font: { size: 12, weight: '500' },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.r.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
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
    createProfitChart();
    createHandStrengthChart();
    createAggressionChart();
    createSessionChart();
    createBankrollChart();
    createStartingHandsChart();
    createHandRangeHeatmap();
    createStreakChart();
    createRadarChart();
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
