"""Pick recording and result entry."""

from database.queries import save_pick, get_pending_picks, update_pick_result, get_pick_history


def record_pick(pick_data):
    """Record a new pick."""
    return save_pick(pick_data)


def get_all_pending():
    """Get all unresolved picks."""
    return get_pending_picks()


def enter_result(pick_id, actual_value):
    """Enter the actual result for a pick."""
    update_pick_result(pick_id, actual_value)


def get_history(limit=100, offset=0):
    """Get pick history."""
    return get_pick_history(limit, offset)
