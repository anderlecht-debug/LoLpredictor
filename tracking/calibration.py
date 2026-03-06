"""Model calibration analysis."""

from database.queries import get_calibration_data


def check_calibration():
    """Check model calibration and return alerts if needed."""
    cal_data = get_calibration_data()
    alerts = []

    for bucket in cal_data:
        predicted = bucket.get('avg_predicted', 0)
        actual = bucket.get('actual_rate', 0)
        total = bucket.get('total', 0)

        if total < 10:
            continue

        diff = abs(predicted - actual)
        if diff > 0.10:
            alerts.append({
                'bucket': bucket['bucket'],
                'predicted': round(predicted, 3),
                'actual': round(actual, 3),
                'diff': round(diff, 3),
                'message': f"Calibration off in {bucket['bucket']} bucket: "
                          f"predicted {predicted:.1%}, actual {actual:.1%}",
            })

    return {
        'calibration_data': cal_data,
        'alerts': alerts,
        'is_calibrated': len(alerts) == 0,
    }
