"""3076. Shortest Uncommon Substring in an Array (Medium).

Specification: https://leetcode.com/problems/shortest-uncommon-substring-in-an-array/description/
"""


def solve(arr: list[str]) -> list[str]:
    answer = []
    for i, s in enumerate(arr):
        best = ""
        for length in range(1, len(s) + 1):
            if best:
                break
            candidates = []
            for start in range(len(s) - length + 1):
                sub = s[start:start + length]
                if all(j == i or sub not in arr[j] for j in range(len(arr))):
                    candidates.append(sub)
            if candidates:
                best = min(candidates)
        answer.append(best)
    return answer


class Solution:
    def shortestSubstrings(self, arr: list[str]) -> list[str]:
        return solve(arr)
