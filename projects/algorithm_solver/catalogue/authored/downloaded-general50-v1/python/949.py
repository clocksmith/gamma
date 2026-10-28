"""949. Largest Time for Given Digits (Medium).

Specification: https://leetcode.com/problems/largest-time-for-given-digits/description/
"""


def solve(arr: list[int]) -> str:
    best = -1
    for i in range(4):
        for j in range(4):
            if j == i:
                continue
            for k in range(4):
                if k == i or k == j:
                    continue
                for l in range(4):
                    if l == i or l == j or l == k:
                        continue
                    hour = arr[i] * 10 + arr[j]
                    minute = arr[k] * 10 + arr[l]
                    if hour < 24 and minute < 60:
                        best = max(best, hour * 60 + minute)
    if best == -1:
        return ''
    return f"{best // 60:02d}:{best % 60:02d}"


class Solution:
    def largestTimeFromDigits(self, arr: list[int]) -> str:
        return solve(arr)
