"""2808. Minimum Seconds to Equalize a Circular Array (Medium).

Specification: https://leetcode.com/problems/minimum-seconds-to-equalize-a-circular-array/description/
"""


def solve(nums):
    n = len(nums)
    positions = {}
    for i, v in enumerate(nums):
        positions.setdefault(v, []).append(i)
    ans = n
    for pos in positions.values():
        max_gap = 0
        for j, cur in enumerate(pos):
            nxt = pos[j + 1] if j + 1 < len(pos) else pos[0] + n
            max_gap = max(max_gap, nxt - cur)
        ans = min(ans, max_gap // 2)
    return ans


class Solution:
    def minimumSeconds(self, *args):
        return solve(*args)
