"""2478. Number of Beautiful Partitions. Prefix-summed dynamic programming over admissible boundaries."""


def solve(s: str, k: int, minLength: int) -> int:
    """O(n*k) time and O(n) space. Inputs are preserved."""
    modulus = 1_000_000_007
    size = len(s)
    prime = set("2357")
    if k * minLength > size or s[0] not in prime or s[-1] in prime:
        return 0
    boundary = [False] * (size + 1)
    boundary[0] = boundary[size] = True
    for index in range(1, size):
        boundary[index] = s[index - 1] not in prime and s[index] in prime
    previous = [0] * (size + 1)
    previous[0] = 1
    for _ in range(k):
        current = [0] * (size + 1)
        running = 0
        for end in range(minLength, size + 1):
            start = end - minLength
            if boundary[start]:
                running = (running + previous[start]) % modulus
            if boundary[end]:
                current[end] = running
        previous = current
    return previous[size]


class Solution:
    def beautifulPartitions(self, s: str, k: int, minLength: int) -> int:
        return solve(s, k, minLength)
