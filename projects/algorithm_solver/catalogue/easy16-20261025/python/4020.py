def solve(n: int, requests: list[int]) -> int:
    """Sum travel from floor zero; n bounds valid requests. O(m) time, O(1) space."""
    floor = 0
    answer = 0
    for destination in requests:
        answer += abs(destination - floor)
        floor = destination
    return answer
