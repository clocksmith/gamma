def solve(s: str) -> int:
    """An alternating arrangement needs counts differing by at most one. O(n)/O(1)."""
    balance = 0
    answer = 0
    for character in s:
        balance += 1 if character == "1" else -1
        if abs(balance) <= 1:
            answer += 1
    return answer
