"""2523. Closest Prime Numbers in Range: sieve the interval ceiling and compare adjacent primes in increasing order."""


def solve(left: int, right: int) -> list[int]:
    """O(right log log(right + 2)) time and O(right) auxiliary space; inputs are read-only."""
    prime = bytearray([1]) * (right + 1)
    prime[0] = 0
    if right >= 1:
        prime[1] = 0
    factor = 2
    while factor * factor <= right:
        if prime[factor]:
            for multiple in range(factor * factor, right + 1, factor):
                prime[multiple] = 0
        factor += 1
    previous = -1
    best_gap = right + 1
    answer = [-1, -1]
    for value in range(max(left, 2), right + 1):
        if not prime[value]:
            continue
        if previous != -1 and value - previous < best_gap:
            best_gap = value - previous
            answer = [previous, value]
        previous = value
    return answer


class Solution:
    def closestPrimes(self, left: int, right: int) -> list[int]:
        return solve(left, right)
