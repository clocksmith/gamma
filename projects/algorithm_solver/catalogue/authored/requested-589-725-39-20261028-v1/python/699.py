"""Original LeetCode 699 candidate; qualification unknown."""

def solve(positions):
    placed, out, high = [], [], 0
    for left, size in positions:
        right = left + size
        base = max((top for a,b,top in placed if a < right and left < b), default=0)
        top = base + size
        placed.append((left, right, top))
        high = max(high, top)
        out.append(high)
    return out


class Solution:
    def fallingSquares(self, positions):
        return solve(positions)
