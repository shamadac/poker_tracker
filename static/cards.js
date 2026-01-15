// Card rendering and visualization functions

function parseCard(cardStr) {
    if (!cardStr || cardStr === 'unknown') return null;
    
    const rank = cardStr.slice(0, -1);
    const suit = cardStr.slice(-1);
    
    return { rank, suit };
}

function getSuitSymbol(suit) {
    const suits = {
        'h': '♥',
        'd': '♦',
        'c': '♣',
        's': '♠'
    };
    return suits[suit.toLowerCase()] || suit;
}

function getSuitColor(suit) {
    return (suit.toLowerCase() === 'h' || suit.toLowerCase() === 'd') ? 'red' : 'black';
}

function renderCard(cardStr) {
    const card = parseCard(cardStr);
    if (!card) return '<span class="card-display">??</span>';
    
    const color = getSuitColor(card.suit);
    const symbol = getSuitSymbol(card.suit);
    
    return `
        <span class="card-display">
            <div class="playing-card ${color}">
                <div class="card-rank">${card.rank}</div>
                <div class="card-suit">${symbol}</div>
            </div>
        </span>
    `;
}

function renderCards(cardsStr) {
    if (!cardsStr || cardsStr === 'unknown') return '<span>No cards</span>';
    
    const cards = cardsStr.split(' ');
    return cards.map(card => renderCard(card)).join('');
}

function renderBoardCards(board) {
    let html = '<div class="board-cards">';
    
    if (board.flop) {
        html += `
            <div class="street-section">
                <span class="street-label">Flop:</span>
                ${renderCards(board.flop)}
            </div>
        `;
    }
    
    if (board.turn) {
        html += `
            <div class="street-section">
                <span class="street-label">Turn:</span>
                ${renderCard(board.turn)}
            </div>
        `;
    }
    
    if (board.river) {
        html += `
            <div class="street-section">
                <span class="street-label">River:</span>
                ${renderCard(board.river)}
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

function renderBettingRounds(rounds, playerName = 'Z420909') {
    let html = '<div class="betting-rounds">';
    
    const streets = ['preflop', 'flop', 'turn', 'river'];
    
    for (const street of streets) {
        const actions = rounds[street];
        if (actions && actions.length > 0) {
            html += `<h4 style="margin-top: 15px; color: #2a5298;">${street.charAt(0).toUpperCase() + street.slice(1)}</h4>`;
            
            for (const action of actions) {
                const isPlayer = action.includes(playerName);
                html += `<div class="betting-action ${isPlayer ? 'player-action' : ''}">${action}</div>`;
            }
        }
    }
    
    html += '</div>';
    return html;
}

function renderHandDetails(details) {
    let html = '<div class="hand-visualizer">';
    
    // Board cards
    if (details.board && (details.board.flop || details.board.turn || details.board.river)) {
        html += '<h3>Community Cards</h3>';
        html += renderBoardCards(details.board);
    }
    
    // Pot size
    if (details.pot_size && details.pot_size !== '0') {
        html += `<div class="pot-info">💰 Pot: $${details.pot_size}</div>`;
    }
    
    // Players
    if (details.players && details.players.length > 0) {
        html += '<h3 style="margin-top: 20px;">Players</h3>';
        html += '<table class="players-table">';
        html += '<tr><th>Seat</th><th>Player</th><th>Stack</th></tr>';
        
        for (const player of details.players) {
            html += `<tr>
                <td>${player.seat}</td>
                <td>${player.name}</td>
                <td>$${player.stack}</td>
            </tr>`;
        }
        
        html += '</table>';
    }
    
    // Betting rounds
    if (details.betting_rounds) {
        html += '<h3 style="margin-top: 20px;">Action</h3>';
        html += renderBettingRounds(details.betting_rounds);
    }
    
    // Showdown
    if (details.showdown && details.showdown.length > 0) {
        html += '<div class="showdown-section">';
        html += '<h4>🎯 Showdown</h4>';
        
        for (const show of details.showdown) {
            html += `<div style="margin: 10px 0;">
                <strong>${show.player}</strong> shows: ${renderCards(show.cards)}
            </div>`;
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

function renderPlaystyleReport(report, recommendations) {
    let html = '<div class="playstyle-report">';
    html += '<h2 style="text-align: center; color: #1e3c72; margin-bottom: 30px;">📊 Comprehensive Playstyle Analysis</h2>';
    
    // Statistics grid
    html += '<div class="stat-grid">';
    
    html += `
        <div class="stat-box">
            <div class="stat-label">VPIP</div>
            <div class="stat-value">${report.vpip}%</div>
            <div class="stat-label">Voluntarily Put $ In Pot</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">PFR</div>
            <div class="stat-value">${report.pfr}%</div>
            <div class="stat-label">Pre-Flop Raise</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Aggression</div>
            <div class="stat-value">${report.aggression}</div>
            <div class="stat-label">Aggression Factor</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Win Rate</div>
            <div class="stat-value">${report.win_rate.win_percentage}%</div>
            <div class="stat-label">${report.win_rate.wins}W / ${report.win_rate.losses}L / ${report.win_rate.folds}F</div>
        </div>
    `;
    
    html += '</div>';
    
    // Strengths
    if (report.strengths && report.strengths.length > 0) {
        html += '<div class="strengths-section">';
        html += '<div class="section-title">✅ Strengths</div>';
        for (const strength of report.strengths) {
            html += `<div class="list-item">${strength}</div>`;
        }
        html += '</div>';
    }
    
    // Mistakes
    if (report.common_mistakes && report.common_mistakes.length > 0) {
        html += '<div class="mistakes-section">';
        html += '<div class="section-title">⚠️ Areas for Improvement</div>';
        for (const mistake of report.common_mistakes) {
            html += `<div class="list-item">${mistake}</div>`;
        }
        html += '</div>';
    }
    
    // AI Recommendations
    if (recommendations) {
        html += '<div class="recommendations-section">';
        html += '<div class="section-title">🎯 AI Coach Recommendations</div>';
        html += `<div style="white-space: pre-wrap; line-height: 1.8;">${recommendations}</div>`;
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}
