def solve(n: int, x: int) -> bool:
    """Check decimal membership and the leading digit. O(d) time and space."""
    digits = str(n)
    digit = str(x)
    return digits[0] != digit and digit in digits
