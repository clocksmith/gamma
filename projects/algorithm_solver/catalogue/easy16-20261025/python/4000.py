def solve(n: int, s: int) -> int:
    """Put available digit sum at the highest places first. O(n) time, O(1) space."""
    if s > 9 * n:
        return -1
    answer = 0
    for _ in range(n):
        digit = min(9, s)
        answer = 10 * answer + digit
        s -= digit
    return answer
