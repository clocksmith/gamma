def solve(s: str) -> bool:
    """Check adjacent decimal digits. O(n) time, O(1) auxiliary space."""
    for index in range(1, len(s)):
        if abs(ord(s[index]) - ord(s[index - 1])) > 2:
            return False
    return True
