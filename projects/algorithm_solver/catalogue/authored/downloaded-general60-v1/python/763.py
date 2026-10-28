"""763. Partition Labels (Medium).

Specification: https://leetcode.com/problems/partition-labels/description/
"""


def solve(s: str) -> list[int]:
    last = {ch: i for i, ch in enumerate(s)}
    result = []
    start = 0
    end = 0
    for i, ch in enumerate(s):
        end = max(end, last[ch])
        if i == end:
            result.append(end - start + 1)
            start = i + 1
    return result


class Solution:
    def partitionLabels(self, s: str) -> list[int]:
        return solve(s)
