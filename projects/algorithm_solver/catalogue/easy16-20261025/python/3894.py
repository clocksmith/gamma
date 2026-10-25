def solve(timer: int) -> str:
    """Return the signal color. O(1) time and auxiliary space."""
    if timer == 0:
        return "Green"
    if timer == 30:
        return "Orange"
    if 30 < timer <= 90:
        return "Red"
    return "Invalid"
