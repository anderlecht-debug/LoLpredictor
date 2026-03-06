/* LoL Props Lab - Main Application Logic */

const App = {
    currentView: 'dashboard',
    selectedMatchId: null,
    matchData: {},
    teams: [],
    leagues: [],

    init() {
        this.bindNavigation();
        this.bindMatchModal();
        this.loadInitialData();
        this.bindKeyboardShortcuts();
    },

    // --- Navigation ---
    bindNavigation() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchView(tab.dataset.view);
            });
        });
    },

    switchView(view) {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.querySelector(`[data-view="${view}"]`).classList.add('active');
        document.getElementById(`view-${view}`).classList.add('active');
        this.currentView = view;

        if (view === 'bestpicks') this.loadBestPicks();
        if (view === 'results') this.loadResults();
        if (view === 'settings') this.loadSettings();
    },

    // --- Initial Data Load ---
    async loadInitialData() {
        try {
            const [teams, leagues, status] = await Promise.all([
                this.api('/api/teams'),
                this.api('/api/leagues'),
                this.api('/api/data/status'),
            ]);
            this.teams = teams || [];
            this.leagues = leagues || [];
            this.updateFreshness(status);
            this.populateAutocomplete();
            this.loadMatches();
        } catch (e) {
            console.error('Failed to load initial data:', e);
        }

        document.getElementById('refresh-btn').addEventListener('click', () => this.refreshData());
    },

    updateFreshness(status) {
        const badge = document.getElementById('data-freshness');
        if (!status || !status.latest_date) {
            badge.textContent = 'No data';
            badge.className = 'freshness-badge';
            return;
        }
        const latest = new Date(status.latest_date);
        const now = new Date();
        const days = Math.floor((now - latest) / (1000 * 60 * 60 * 24));

        badge.textContent = `Data: ${status.latest_date}`;
        if (days <= 2) {
            badge.className = 'freshness-badge fresh';
        } else if (days <= 5) {
            badge.className = 'freshness-badge stale';
        } else {
            badge.className = 'freshness-badge old';
        }
    },

    populateAutocomplete() {
        const teamListA = document.getElementById('team-suggestions-a');
        const teamListB = document.getElementById('team-suggestions-b');
        const leagueList = document.getElementById('league-suggestions');

        this.teams.forEach(t => {
            teamListA.appendChild(new Option(t));
            teamListB.appendChild(new Option(t));
        });

        const leagueNames = [...new Set(this.leagues.map(l => l.league))];
        leagueNames.forEach(l => leagueList.appendChild(new Option(l)));

        // Also populate filter dropdowns
        const filterLeague = document.getElementById('filter-league');
        leagueNames.forEach(l => {
            const opt = document.createElement('option');
            opt.value = l;
            opt.textContent = l;
            filterLeague.appendChild(opt);
        });
    },

    // --- Match Management ---
    async loadMatches() {
        const matches = await this.api('/api/matches');
        const list = document.getElementById('match-list');

        if (!matches || matches.length === 0) {
            list.innerHTML = '<p class="empty-state">No matches added yet. Click "+ Add Match" to get started.</p>';
            return;
        }

        list.innerHTML = matches.map(m => `
            <div class="match-card ${m.match_id === this.selectedMatchId ? 'selected' : ''}"
                 data-id="${m.match_id}">
                <button class="match-delete" data-id="${m.match_id}" title="Delete match">&times;</button>
                <div class="match-league">${m.league} &middot; ${m.format || 'Bo1'}</div>
                <div class="match-teams">${m.team_a} vs ${m.team_b}</div>
                <div class="match-date">${m.match_date || 'No date set'}</div>
            </div>
        `).join('');

        list.querySelectorAll('.match-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.classList.contains('match-delete')) return;
                this.selectMatch(parseInt(card.dataset.id));
            });
        });

        list.querySelectorAll('.match-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                await this.api(`/api/matches/${id}`, 'DELETE');
                if (this.selectedMatchId === id) {
                    this.selectedMatchId = null;
                    document.getElementById('projections-content').innerHTML =
                        '<p class="empty-state">Select a match to view projections.</p>';
                    document.getElementById('context-panel').style.display = 'none';
                }
                this.loadMatches();
                this.toast('Match deleted');
            });
        });
    },

    bindMatchModal() {
        const modal = document.getElementById('add-match-modal');
        document.getElementById('add-match-btn').addEventListener('click', () => {
            modal.style.display = 'flex';
        });
        document.getElementById('cancel-match-btn').addEventListener('click', () => {
            modal.style.display = 'none';
        });
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.style.display = 'none';
        });
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });
        document.getElementById('save-match-btn').addEventListener('click', () => this.saveMatch());
    },

    async saveMatch() {
        const data = {
            league: document.getElementById('match-league').value.trim(),
            team_a: document.getElementById('match-team-a').value.trim(),
            team_b: document.getElementById('match-team-b').value.trim(),
            match_date: document.getElementById('match-date').value || null,
            format: document.getElementById('match-format').value,
        };

        if (!data.league || !data.team_a || !data.team_b) {
            this.toast('Please fill in league and both teams', 'error');
            return;
        }

        await this.api('/api/matches', 'POST', data);
        document.getElementById('add-match-modal').style.display = 'none';

        // Clear form
        ['match-league', 'match-team-a', 'match-team-b', 'match-date'].forEach(id => {
            document.getElementById(id).value = '';
        });

        this.loadMatches();
        this.toast('Match added');
    },

    async selectMatch(matchId) {
        this.selectedMatchId = matchId;

        // Update selection UI
        document.querySelectorAll('.match-card').forEach(c => c.classList.remove('selected'));
        const card = document.querySelector(`.match-card[data-id="${matchId}"]`);
        if (card) card.classList.add('selected');

        // Load projections
        document.getElementById('projections-content').innerHTML =
            '<p class="empty-state">Loading projections...</p>';

        try {
            const data = await this.api(`/api/matches/${matchId}/projections`);
            this.matchData = data;
            this.renderProjections(data);
            this.renderContext(data);
        } catch (e) {
            document.getElementById('projections-content').innerHTML =
                '<p class="empty-state">Failed to load projections. Make sure you have data imported.</p>';
        }
    },

    // --- Projections Rendering ---
    renderProjections(data) {
        const container = document.getElementById('projections-content');
        const match = data.match;
        const players = data.players || [];

        document.getElementById('match-info').textContent =
            `${match.team_a} vs ${match.team_b} | ${match.league}`;

        if (players.length === 0) {
            container.innerHTML = '<p class="empty-state">No player data found for these teams. Try refreshing data.</p>';
            return;
        }

        // Group players by team
        const teamA = players.filter(p => p.team === match.team_a);
        const teamB = players.filter(p => p.team === match.team_b);

        const html = `
            ${this.renderTeamSection(teamA, match.team_a, 'blue', data)}
            ${this.renderTeamSection(teamB, match.team_b, 'red', data)}
        `;
        container.innerHTML = html;
        this.bindLineInputs();
    },

    renderTeamSection(players, teamName, side, data) {
        const posOrder = ['top', 'jng', 'mid', 'bot', 'sup'];
        players.sort((a, b) => posOrder.indexOf(a.position) - posOrder.indexOf(b.position));

        return `
            <div class="team-section">
                <div class="team-header ${side}">
                    <span>${side.toUpperCase()} SIDE</span>
                    <span>${teamName}</span>
                </div>
                ${players.map(p => this.renderPlayerGroup(p, data)).join('')}
            </div>
        `;
    },

    renderPlayerGroup(player, data) {
        const stats = ['kills', 'deaths', 'assists', 'cs'];
        const lines = data.entered_lines || {};
        const edges = player.edges || {};

        return `
            <div class="player-group">
                <div class="player-name-row">
                    <span class="role-badge">${player.position}</span>
                    <span>${player.playername}</span>
                    <span class="confidence-badge confidence-${player.confidence}">${player.confidence}</span>
                </div>
                ${stats.map(stat => {
                    const proj = player.projections[stat];
                    const lineKey = `${player.playername}_${stat}`;
                    const lineVal = lines[lineKey] || '';
                    const edge = edges[stat];

                    return `
                        <div class="stat-row">
                            <span class="stat-label">${stat}</span>
                            <span class="stat-projection">${proj ? proj.mean.toFixed(1) : '-'}</span>
                            <span class="stat-std">&plusmn;${proj ? proj.std.toFixed(1) : '-'}</span>
                            <input type="number" class="line-input" step="0.5"
                                   data-player="${player.playername}" data-stat="${stat}"
                                   data-match-id="${this.selectedMatchId}"
                                   value="${lineVal}" placeholder="Line">
                            <span class="direction-badge ${edge ? edge.direction : ''}">${edge ? edge.direction.toUpperCase() : '-'}</span>
                            <span class="edge-value ${edge ? this.edgeClass(edge.edge) : ''}">${edge ? (edge.edge * 100).toFixed(1) + '%' : '-'}</span>
                            <span>${edge ? (edge.probability * 100).toFixed(0) + '%' : '-'}</span>
                            <span class="confidence-badge confidence-${edge ? edge.confidence : ''}">${edge ? edge.confidence : '-'}</span>
                            <span>${edge && edge.recommended ? '<span class="recommend-check">&#10003;</span>' : ''}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    bindLineInputs() {
        document.querySelectorAll('.line-input').forEach(input => {
            let debounceTimer;
            input.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => this.submitLine(input), 400);
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    input.value = (parseFloat(input.value || 0) + 0.5).toFixed(1);
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => this.submitLine(input), 400);
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    input.value = Math.max(0, parseFloat(input.value || 0) - 0.5).toFixed(1);
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => this.submitLine(input), 400);
                }
            });
        });
    },

    async submitLine(input) {
        const value = parseFloat(input.value);
        if (isNaN(value) || value <= 0) return;

        const data = {
            match_id: parseInt(input.dataset.matchId),
            player: input.dataset.player,
            stat: input.dataset.stat,
            line_value: value,
        };

        try {
            const result = await this.api('/api/lines', 'POST', data);
            // Re-render to update edge display
            if (this.selectedMatchId) {
                this.selectMatch(this.selectedMatchId);
            }
        } catch (e) {
            console.error('Failed to submit line:', e);
        }
    },

    // --- Context Panel ---
    renderContext(data) {
        const ctx = data.match_context;
        if (!ctx) return;

        const panel = document.getElementById('context-panel');
        panel.style.display = '';

        const pace = ctx.pace || {};
        const gl = ctx.game_length || {};
        const wp = ctx.win_probability || {};
        const match = data.match;

        document.getElementById('context-content').innerHTML = `
            <div class="context-item">
                <div class="context-label">Expected Pace</div>
                <div class="context-value ${(pace.label || '').toLowerCase()}">${pace.label || 'N/A'}</div>
                <div style="color:var(--text-tertiary);font-size:12px;margin-top:2px">
                    ${pace.combined_kpm ? pace.combined_kpm.toFixed(2) + ' KPM' : ''}
                    ${pace.league_avg_kpm ? '(avg: ' + pace.league_avg_kpm.toFixed(2) + ')' : ''}
                </div>
            </div>
            <div class="context-item">
                <div class="context-label">Expected Game Length</div>
                <div class="context-value">${gl.expected_minutes ? gl.expected_minutes.toFixed(1) + ' min' : 'N/A'}</div>
                <div style="color:var(--text-tertiary);font-size:12px;margin-top:2px">
                    ${gl.league_avg_minutes ? 'League avg: ' + gl.league_avg_minutes.toFixed(1) + ' min' : ''}
                </div>
            </div>
            <div class="context-item">
                <div class="context-label">Win Probability</div>
                <div class="win-prob-bar">
                    <div class="team-a" style="width:${(wp.team_a || 0.5) * 100}%">
                        ${match.team_a} ${((wp.team_a || 0.5) * 100).toFixed(0)}%
                    </div>
                    <div class="team-b" style="width:${(wp.team_b || 0.5) * 100}%">
                        ${match.team_b} ${((wp.team_b || 0.5) * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
        `;
    },

    // --- Best Picks ---
    async loadBestPicks() {
        const container = document.getElementById('bestpicks-table-container');
        try {
            const data = await this.api('/api/best-picks');
            const picks = data.picks || [];

            if (picks.length === 0) {
                container.innerHTML = '<p class="empty-state">Enter lines on the Dashboard to see recommendations here.</p>';
                document.getElementById('parlay-suggestions').style.display = 'none';
                return;
            }

            // Apply filters
            const leagueFilter = document.getElementById('filter-league').value;
            const statFilter = document.getElementById('filter-stat').value;
            const confFilter = document.getElementById('filter-confidence').value;

            let filtered = picks;
            if (leagueFilter) filtered = filtered.filter(p => p.league === leagueFilter);
            if (statFilter) filtered = filtered.filter(p => p.stat === statFilter);
            if (confFilter) filtered = filtered.filter(p => p.confidence === confFilter);

            container.innerHTML = `
                <table class="picks-table">
                    <thead>
                        <tr>
                            <th>#</th><th>Player</th><th>Matchup</th><th>League</th>
                            <th>Stat</th><th>Line</th><th>Dir</th><th>Proj</th>
                            <th>Prob</th><th>Edge</th><th>Conf</th><th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${filtered.map((p, i) => `
                            <tr class="${p.recommended ? 'recommended-row' : ''}">
                                <td>${i + 1}</td>
                                <td><strong>${p.playername}</strong></td>
                                <td>${p.team} vs ${p.opponent}</td>
                                <td>${p.league}</td>
                                <td>${p.stat}</td>
                                <td style="font-family:var(--font-mono)">${p.line}</td>
                                <td><span class="direction-badge ${p.direction}">${p.direction.toUpperCase()}</span></td>
                                <td style="font-family:var(--font-mono)">${p.projection.toFixed(1)}</td>
                                <td style="font-family:var(--font-mono)">${(p.probability * 100).toFixed(0)}%</td>
                                <td class="edge-value ${this.edgeClass(p.edge)}">${(p.edge * 100).toFixed(1)}%</td>
                                <td><span class="confidence-badge confidence-${p.confidence}">${p.confidence}</span></td>
                                <td><button class="btn btn-sm btn-primary pick-btn" data-pick='${JSON.stringify(p)}'>Save Pick</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            // Bind save pick buttons
            container.querySelectorAll('.pick-btn').forEach(btn => {
                btn.addEventListener('click', () => this.savePick(JSON.parse(btn.dataset.pick)));
            });

            // Render parlay suggestions
            this.renderParlays(data.parlays);

            // Bind filter change events
            ['filter-league', 'filter-stat', 'filter-confidence'].forEach(id => {
                document.getElementById(id).onchange = () => this.loadBestPicks();
            });
        } catch (e) {
            container.innerHTML = '<p class="empty-state">Failed to load picks.</p>';
        }
    },

    renderParlays(parlays) {
        if (!parlays) return;
        const section = document.getElementById('parlay-suggestions');
        const content = document.getElementById('parlay-content');

        const indep = parlays.independent_parlay;
        const stack = parlays.correlated_stack;

        if ((!indep || !indep.picks || indep.picks.length === 0) && !stack) {
            section.style.display = 'none';
            return;
        }

        section.style.display = '';
        let html = '';

        if (indep && indep.picks && indep.picks.length > 0) {
            html += `
                <div class="parlay-card">
                    <h4>Best Independent Parlay (${indep.picks.length}-pick)</h4>
                    ${indep.picks.map(p => `
                        <div class="parlay-pick">
                            <strong>${p.playername}</strong>
                            <span>${p.stat} ${p.direction.toUpperCase()} ${p.line}</span>
                            <span class="edge-value ${this.edgeClass(p.edge)}">${(p.edge * 100).toFixed(1)}%</span>
                        </div>
                    `).join('')}
                    ${indep.combined_probability ?
                        `<div style="margin-top:8px;color:var(--text-secondary);font-size:12px">
                            Combined probability: ${(indep.combined_probability * 100).toFixed(1)}%
                        </div>` : ''}
                </div>
            `;
        }

        if (stack) {
            html += `
                <div class="parlay-card">
                    <h4>Best Correlated Stack: ${stack.match}</h4>
                    ${stack.picks.map(p => `
                        <div class="parlay-pick">
                            <strong>${p.playername}</strong>
                            <span>${p.stat} ${p.direction.toUpperCase()} ${p.line}</span>
                            <span class="edge-value ${this.edgeClass(p.edge)}">${(p.edge * 100).toFixed(1)}%</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        content.innerHTML = html;
    },

    async savePick(pick) {
        const data = {
            playername: pick.playername,
            stat: pick.stat,
            line: pick.line,
            direction: pick.direction,
            model_projection: pick.projection,
            model_probability: pick.probability,
            edge: pick.edge,
            confidence: pick.confidence,
            league: pick.league,
            match_date: null,
        };
        await this.api('/api/picks', 'POST', data);
        this.toast('Pick saved!', 'success');
    },

    // --- Results ---
    async loadResults() {
        try {
            const [dashboard, pending, history] = await Promise.all([
                this.api('/api/performance/summary'),
                this.api('/api/picks/pending'),
                this.api('/api/performance/history?limit=50'),
            ]);

            this.renderSummaryCards(dashboard.summary);
            this.renderPerformanceCharts(dashboard);
            this.renderPendingPicks(pending);
            this.renderPickHistory(history);
        } catch (e) {
            console.error('Failed to load results:', e);
        }
    },

    renderSummaryCards(summary) {
        const container = document.getElementById('performance-summary');
        if (!summary) {
            container.innerHTML = '<p class="empty-state" style="grid-column:1/-1">No picks recorded yet.</p>';
            return;
        }
        container.innerHTML = `
            <div class="summary-card">
                <div class="card-label">Total Picks</div>
                <div class="card-value">${summary.total_picks || 0}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Hits</div>
                <div class="card-value" style="color:var(--accent-green)">${summary.hits || 0}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Misses</div>
                <div class="card-value" style="color:var(--accent-red)">${summary.misses || 0}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Hit Rate</div>
                <div class="card-value">${summary.hit_rate ? (summary.hit_rate * 100).toFixed(1) + '%' : 'N/A'}</div>
            </div>
        `;
    },

    renderPerformanceCharts(dashboard) {
        const container = document.getElementById('results-charts');
        const byStat = dashboard.by_stat || [];
        const byLeague = dashboard.by_league || [];

        let html = '';

        if (byStat.length > 0) {
            html += `
                <div class="chart-card">
                    <h4>Hit Rate by Stat</h4>
                    <div class="bar-chart">
                        ${byStat.map(s => `
                            <div class="bar-row">
                                <div class="bar-label">${s.stat}</div>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:${(s.hit_rate || 0) * 100}%;background:${s.hit_rate >= 0.5 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                        ${s.hit_rate ? (s.hit_rate * 100).toFixed(0) + '%' : '0%'} (${s.total})
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (byLeague.length > 0) {
            html += `
                <div class="chart-card">
                    <h4>Hit Rate by League</h4>
                    <div class="bar-chart">
                        ${byLeague.map(l => `
                            <div class="bar-row">
                                <div class="bar-label">${l.league}</div>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:${(l.hit_rate || 0) * 100}%;background:${l.hit_rate >= 0.5 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                        ${l.hit_rate ? (l.hit_rate * 100).toFixed(0) + '%' : '0%'} (${l.total})
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Calibration chart
        const cal = dashboard.calibration || [];
        if (cal.length > 0) {
            html += `
                <div class="chart-card">
                    <h4>Model Calibration</h4>
                    <div class="bar-chart">
                        ${cal.map(c => `
                            <div class="bar-row">
                                <div class="bar-label">${c.bucket}</div>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:${(c.actual_rate || 0) * 100}%;background:var(--accent-purple)">
                                        Actual: ${c.actual_rate ? (c.actual_rate * 100).toFixed(0) + '%' : 'N/A'} (n=${c.total})
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html || '<p class="empty-state">No performance data yet.</p>';
    },

    renderPendingPicks(picks) {
        const container = document.getElementById('pending-picks-table');
        if (!picks || picks.length === 0) {
            container.innerHTML = '<p class="empty-state">No pending picks.</p>';
            return;
        }

        container.innerHTML = `
            <table class="picks-table">
                <thead>
                    <tr><th>Date</th><th>Player</th><th>Stat</th><th>Line</th><th>Dir</th><th>Proj</th><th>Edge</th><th>Actual</th><th></th></tr>
                </thead>
                <tbody>
                    ${picks.map(p => `
                        <tr>
                            <td>${p.date_entered}</td>
                            <td><strong>${p.playername}</strong></td>
                            <td>${p.stat}</td>
                            <td>${p.line}</td>
                            <td><span class="direction-badge ${p.direction}">${p.direction.toUpperCase()}</span></td>
                            <td>${p.model_projection.toFixed(1)}</td>
                            <td class="edge-value ${this.edgeClass(p.edge)}">${(p.edge * 100).toFixed(1)}%</td>
                            <td><input type="number" class="line-input result-input" data-pick-id="${p.pick_id}" step="1" placeholder="Actual"></td>
                            <td><button class="btn btn-sm submit-result-btn" data-pick-id="${p.pick_id}">Submit</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        container.querySelectorAll('.submit-result-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const pickId = parseInt(btn.dataset.pickId);
                const input = container.querySelector(`.result-input[data-pick-id="${pickId}"]`);
                const actual = parseFloat(input.value);
                if (isNaN(actual)) {
                    this.toast('Enter actual value', 'error');
                    return;
                }
                await this.api('/api/results', 'POST', { pick_id: pickId, actual_result: actual });
                this.toast('Result submitted', 'success');
                this.loadResults();
            });
        });
    },

    renderPickHistory(picks) {
        const container = document.getElementById('pick-history-table');
        if (!picks || picks.length === 0) {
            container.innerHTML = '<p class="empty-state">No pick history yet.</p>';
            return;
        }

        container.innerHTML = `
            <table class="picks-table">
                <thead>
                    <tr><th>Date</th><th>Player</th><th>Stat</th><th>Line</th><th>Dir</th><th>Proj</th><th>Edge</th><th>Actual</th><th>Result</th></tr>
                </thead>
                <tbody>
                    ${picks.map(p => `
                        <tr>
                            <td>${p.date_entered}</td>
                            <td><strong>${p.playername}</strong></td>
                            <td>${p.stat}</td>
                            <td>${p.line}</td>
                            <td><span class="direction-badge ${p.direction}">${p.direction.toUpperCase()}</span></td>
                            <td>${p.model_projection.toFixed(1)}</td>
                            <td class="edge-value ${this.edgeClass(p.edge)}">${(p.edge * 100).toFixed(1)}%</td>
                            <td>${p.actual_result != null ? p.actual_result : '-'}</td>
                            <td>${p.hit != null ? (p.hit ? '<span style="color:var(--accent-green)">HIT</span>' : '<span style="color:var(--accent-red)">MISS</span>') : '<span style="color:var(--text-tertiary)">Pending</span>'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    // --- Settings ---
    async loadSettings() {
        const [settings, status] = await Promise.all([
            this.api('/api/settings'),
            this.api('/api/data/status'),
        ]);

        this.renderSettingsForm(settings);
        this.renderDataStatus(status);
    },

    renderSettingsForm(settings) {
        const container = document.getElementById('model-params-form');
        const paramLabels = {
            LOOKBACK_WINDOW: 'Lookback Window (games)',
            DECAY_FACTOR: 'Decay Factor',
            MIN_GAMES_PLAYER: 'Min Games for Player',
            MIN_GAMES_OPPONENT: 'Min Games for Opponent',
            PACE_EXPONENT_KILLS: 'Pace Exponent (Kills)',
            PACE_EXPONENT_ASSISTS: 'Pace Exponent (Assists)',
            GAMELENGTH_EXPONENT_CS: 'Game Length Exponent (CS)',
            GAMELENGTH_EXPONENT_KDA: 'Game Length Exponent (KDA)',
            LOW_CONF_STD_MULTIPLIER: 'Low Confidence Std Multiplier',
            EDGE_THRESHOLD_RECOMMEND: 'Edge Threshold (Recommend)',
            EDGE_THRESHOLD_HIGH_CONF: 'Edge Threshold (High Conf)',
        };

        container.innerHTML = Object.entries(paramLabels).map(([key, label]) => `
            <div class="form-group">
                <label>${label}</label>
                <input type="number" class="form-input setting-input" data-key="${key}"
                       value="${settings[key] || ''}" step="0.01">
            </div>
        `).join('');

        document.getElementById('save-settings-btn').onclick = async () => {
            const data = {};
            container.querySelectorAll('.setting-input').forEach(input => {
                data[input.dataset.key] = parseFloat(input.value);
            });
            await this.api('/api/settings', 'PUT', data);
            this.toast('Settings saved', 'success');
        };
    },

    renderDataStatus(status) {
        const container = document.getElementById('data-status-panel');
        if (!status) {
            container.innerHTML = '<p>No data loaded.</p>';
            return;
        }
        container.innerHTML = `
            <div class="form-group">
                <label>Total Games</label>
                <div style="font-family:var(--font-mono);font-size:18px">${status.games || 0}</div>
            </div>
            <div class="form-group">
                <label>Total Players</label>
                <div style="font-family:var(--font-mono);font-size:18px">${status.players || 0}</div>
            </div>
            <div class="form-group">
                <label>Date Range</label>
                <div style="font-size:13px;color:var(--text-secondary)">${status.earliest_date || 'N/A'} to ${status.latest_date || 'N/A'}</div>
            </div>
            <div class="form-group">
                <label>Last Refresh</label>
                <div style="font-size:13px;color:var(--text-secondary)">${status.last_refresh ? status.last_refresh.timestamp : 'Never'}</div>
            </div>
        `;

        document.getElementById('refresh-data-btn').onclick = () => this.refreshData();
    },

    // --- Data Refresh ---
    async refreshData() {
        this.toast('Data refresh started... this may take a few minutes.');
        try {
            await this.api('/api/refresh', 'POST');
            this.toast('Data refresh initiated', 'success');
        } catch (e) {
            this.toast('Failed to start refresh', 'error');
        }
    },

    // --- Keyboard Shortcuts ---
    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
            switch (e.key) {
                case '1': this.switchView('dashboard'); break;
                case '2': this.switchView('bestpicks'); break;
                case '3': this.switchView('results'); break;
                case '4': this.switchView('settings'); break;
            }
        });
    },

    // --- Utility ---
    edgeClass(edge) {
        if (edge >= 0.10) return 'edge-strong';
        if (edge >= 0.05) return 'edge-moderate';
        if (edge >= 0.03) return 'edge-marginal';
        if (edge >= 0) return 'edge-none';
        return 'edge-wrong';
    },

    async api(url, method = 'GET', body = null) {
        const opts = { method, headers: {} };
        if (body) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
        const resp = await fetch(url, opts);
        if (!resp.ok) throw new Error(`API error: ${resp.status}`);
        return resp.json();
    },

    toast(message, type = '') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
