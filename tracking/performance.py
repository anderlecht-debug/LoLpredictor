"""Performance metrics calculation."""

from database.queries import (
    get_performance_summary, get_performance_by_stat,
    get_performance_by_league, get_calibration_data,
    get_pick_history,
)


def get_summary():
    """Get overall performance summary."""
    return get_performance_summary()


def get_by_stat():
    """Get performance broken down by stat type."""
    return get_performance_by_stat()


def get_by_league():
    """Get performance broken down by league."""
    return get_performance_by_league()


def get_calibration():
    """Get calibration data for chart."""
    return get_calibration_data()


def get_full_dashboard():
    """Get all performance data for the dashboard."""
    return {
        'summary': get_summary(),
        'by_stat': get_by_stat(),
        'by_league': get_by_league(),
        'calibration': get_calibration(),
    }
