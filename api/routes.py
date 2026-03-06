"""Flask API routes for LoL Props Lab."""

from flask import Blueprint, jsonify, request
from database.db import get_settings, update_settings
from database.queries import (
    get_all_leagues, get_upcoming_matches, get_match_by_id,
    create_match, delete_match, save_line, get_lines_for_match,
    save_pick, get_pending_picks, update_pick_result,
    get_all_team_names, get_data_status, get_pick_history,
)
from engine.projections import project_match, calculate_edge_for_line
from recommendations.ranker import rank_picks
from recommendations.correlations import detect_correlations
from recommendations.parlays import suggest_parlays
from tracking.performance import get_full_dashboard
from tracking.calibration import check_calibration

api = Blueprint('api', __name__, url_prefix='/api')


# --- League & Team Endpoints ---

@api.route('/leagues')
def leagues():
    return jsonify(get_all_leagues())


@api.route('/teams')
def teams():
    return jsonify(get_all_team_names())


# --- Match Endpoints ---

@api.route('/matches', methods=['GET'])
def list_matches():
    return jsonify(get_upcoming_matches())


@api.route('/matches', methods=['POST'])
def add_match():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    required = ['league', 'team_a', 'team_b']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    match_id = create_match(
        data['league'], data['team_a'], data['team_b'],
        data.get('match_date'), data.get('format', 'Bo1')
    )
    return jsonify({'match_id': match_id})


@api.route('/matches/<int:match_id>', methods=['DELETE'])
def remove_match(match_id):
    delete_match(match_id)
    return jsonify({'status': 'deleted'})


# --- Projection Endpoints ---

@api.route('/matches/<int:match_id>/projections')
def match_projections(match_id):
    match = get_match_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    result = project_match(match['team_a'], match['team_b'], match['league'])

    # Include any entered lines
    lines = get_lines_for_match(match_id)
    lines_map = {}
    for line in lines:
        key = f"{line['playername']}_{line['stat']}"
        lines_map[key] = line['line_value']

    # Calculate edges for entered lines
    for player in result.get('players', []):
        player['edges'] = {}
        for stat in ['kills', 'deaths', 'assists', 'cs']:
            key = f"{player['playername']}_{stat}"
            if key in lines_map:
                edge_result = calculate_edge_for_line(player, stat, lines_map[key])
                if edge_result:
                    player['edges'][stat] = edge_result

    result['match'] = match
    result['entered_lines'] = lines_map
    return jsonify(result)


# --- Line Entry Endpoints ---

@api.route('/lines', methods=['POST'])
def submit_line():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    match_id = data.get('match_id')
    playername = data.get('player')
    stat = data.get('stat')
    line_value = data.get('line_value')

    if not all([match_id, playername, stat, line_value is not None]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        line_value = float(line_value)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid line value'}), 400

    # Save the line
    save_line(match_id, playername, stat, line_value)

    # Calculate edge
    match = get_match_by_id(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    result = project_match(match['team_a'], match['team_b'], match['league'])

    # Find the player's projection
    for player in result.get('players', []):
        if player['playername'] == playername:
            edge_result = calculate_edge_for_line(player, stat, line_value)
            if edge_result:
                return jsonify(edge_result)

    return jsonify({'error': 'Player not found in projections'}), 404


# --- Best Picks Endpoint ---

@api.route('/best-picks')
def best_picks():
    matches = get_upcoming_matches()
    all_picks = []

    for match in matches:
        lines = get_lines_for_match(match['match_id'])
        if not lines:
            continue

        result = project_match(match['team_a'], match['team_b'], match['league'])

        for line in lines:
            for player in result.get('players', []):
                if player['playername'] == line['playername']:
                    edge_result = calculate_edge_for_line(
                        player, line['stat'], line['line_value']
                    )
                    if edge_result:
                        edge_result['match_id'] = match['match_id']
                        edge_result['game_count'] = player.get('game_count', 0)
                        all_picks.append(edge_result)

    # Rank and detect correlations
    ranked = rank_picks(all_picks)
    ranked = detect_correlations(ranked)
    parlays = suggest_parlays(ranked)

    return jsonify({
        'picks': ranked,
        'parlays': parlays,
    })


# --- Pick Management Endpoints ---

@api.route('/picks', methods=['POST'])
def record_pick():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    pick_id = save_pick(data)
    return jsonify({'pick_id': pick_id})


@api.route('/picks/pending')
def pending_picks():
    return jsonify(get_pending_picks())


# --- Results Endpoints ---

@api.route('/results', methods=['POST'])
def enter_results():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    results = data if isinstance(data, list) else [data]
    for result in results:
        pick_id = result.get('pick_id')
        actual = result.get('actual_result')
        if pick_id is not None and actual is not None:
            update_pick_result(pick_id, float(actual))

    return jsonify({'status': 'updated', 'count': len(results)})


@api.route('/performance/summary')
def performance_summary():
    dashboard = get_full_dashboard()
    return jsonify(dashboard)


@api.route('/performance/calibration')
def calibration():
    return jsonify(check_calibration())


@api.route('/performance/history')
def pick_history():
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    return jsonify(get_pick_history(limit, offset))


@api.route('/performance/by-stat')
def by_stat():
    from tracking.performance import get_by_stat
    return jsonify(get_by_stat())


@api.route('/performance/by-league')
def by_league():
    from tracking.performance import get_by_league
    return jsonify(get_by_league())


# --- Settings Endpoints ---

@api.route('/settings', methods=['GET'])
def get_model_settings():
    return jsonify(get_settings())


@api.route('/settings', methods=['PUT'])
def update_model_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    update_settings(data)
    return jsonify(get_settings())


# --- Data Status Endpoint ---

@api.route('/data/status')
def data_status():
    return jsonify(get_data_status())


# --- Refresh Endpoint ---

@api.route('/refresh', methods=['POST'])
def trigger_refresh():
    import threading
    from refresh_data import refresh

    def run_refresh():
        try:
            refresh(download=True)
        except Exception as e:
            print(f"Refresh error: {e}")

    thread = threading.Thread(target=run_refresh)
    thread.start()
    return jsonify({'status': 'refresh_started'})
