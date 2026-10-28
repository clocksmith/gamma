"""907. Sum of Subarray Minimums (Medium).

Specification: https://leetcode.com/problems/sum-of-subarray-minimums/description/
"""


def solve(arr: list[int]) -> int:
    MOD = 1000000007
    n = len(arr)
    left = [0] * n
    right = [0] * n
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        left[i] = i + 1 if not stack else i - stack[-1]
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        right[i] = n - i if not stack else stack[-1] - i
        stack.append(i)
    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


class Solution:
    def sumSubarrayMins(self, arr: list[int]) -> int:
        return solve(arr)
