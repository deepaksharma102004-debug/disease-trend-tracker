def detect_trend(values: list) -> str:
    """
    Takes a list of numeric values and returns the trend direction.
    Returns: "worsening" | "improving" | "spike" | "stable"
    """
    if not values or len(values) < 2:
        return "stable"

    values = [v for v in values if v is not None]
    if len(values) < 2:
        return "stable"

    latest   = values[-1]
    previous = values[-2]

    # Spike check: requires 2 consecutive large changes to avoid false alarms
    if len(values) >= 3:
        second_last       = values[-3]
        spike_from_prev   = abs(latest - previous) / (previous + 1e-9) > 0.15
        spike_from_before = abs(previous - second_last) / (second_last + 1e-9) > 0.15
        if spike_from_prev and spike_from_before:
            return "spike"
    else:
        if abs(latest - previous) / (previous + 1e-9) > 0.15:
            return "spike"

    # Overall trend: first vs last value
    first      = values[0]
    change_pct = (latest - first) / (first + 1e-9)

    if change_pct > 0.05:
        return "worsening"
    elif change_pct < -0.05:
        return "improving"
    else:
        return "stable"


def get_risk_badge(trend1: str, trend2: str = "stable") -> str:
    """
    Computes overall risk badge from the first two parameter trends.
    """
    high_signals = {"worsening", "spike"}

    if trend1 in high_signals or trend2 in high_signals:
        return "HIGH"
    elif trend1 == "improving" or trend2 == "improving":
        return "IMPROVING"
    else:
        return "STABLE"