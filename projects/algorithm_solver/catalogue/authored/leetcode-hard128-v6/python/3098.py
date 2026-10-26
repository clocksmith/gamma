"""3098. Find the Sum of Subsequence Powers.

Integrate counts of subsequences above each possible minimum gap; O(k*n^3) time, O(n^2) space. Inputs are preserved; no floating-point products.
"""

def solve(nums: list[int], k: int) -> int:
    values = sorted(nums)
    n = len(values)
    modulus = 1_000_000_007
    gaps = sorted({0} | {values[j] - values[i] for i in range(n) for j in range(i + 1, n)})
    answer = 0
    previous_gap = 0
    for gap in gaps[1:]:
        eligible = [0] * n
        left = 0
        for index in range(n):
            while left < index and values[left] <= values[index] - gap:
                left += 1
            eligible[index] = left
        ways = [1] * n
        for _ in range(2, k + 1):
            prefix = [0]
            for value in ways:
                prefix.append((prefix[-1] + value) % modulus)
            ways = [prefix[count] for count in eligible]
        answer = (answer + (gap - previous_gap) * sum(ways)) % modulus
        previous_gap = gap
    return answer


class Solution:
    def sumOfPowers(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
