"""276. Paint Fence."""
def solve(n: int, k: int) -> int:
    if n == 1:
        return k
    same = k
    different = k * (k - 1)
    for _ in range(3, n + 1):
        same, different = different, (same + different) * (k - 1)
    return same + different

class Solution:
    def numWays(self, n: int, k: int) -> int:
        return solve(n, k)
