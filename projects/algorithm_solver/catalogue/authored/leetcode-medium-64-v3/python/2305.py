"""2305. Fair Distribution of Cookies: partition subset sums with a minimax dynamic program."""


def solve(cookies: list[int], k: int) -> int:
    """O(k * 3^n) time and O(2^n) auxiliary space for n <= 8 bags; inputs are read-only."""
    size = 1 << len(cookies)
    sums = [0] * size
    for mask in range(1, size):
        bit = mask & -mask
        sums[mask] = sums[mask ^ bit] + cookies[bit.bit_length() - 1]
    best = [float('inf')] * size
    best[0] = 0
    for _ in range(k):
        following = best.copy()
        for mask in range(1, size):
            subset = mask
            while subset:
                following[mask] = min(following[mask], max(best[mask ^ subset], sums[subset]))
                subset = (subset - 1) & mask
        best = following
    return best[-1]


class Solution:
    def distributeCookies(self, cookies: list[int], k: int) -> int:
        return solve(cookies, k)
