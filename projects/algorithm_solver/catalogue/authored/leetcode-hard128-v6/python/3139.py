"""3139. Minimum Cost to Equalize Array.

Evaluate the boundary between unbalanced deficits and pairable deficits, including parity neighbors; O(n) time, O(1) space. Exact integer costs precede modulo.
"""

def solve(nums: list[int], cost1: int, cost2: int) -> int:
    n, total, minimum, maximum = len(nums), sum(nums), min(nums), max(nums)
    modulus = 1_000_000_007
    if n <= 2 or cost2 >= 2 * cost1:
        return ((n * maximum - total) * cost1) % modulus
    boundary = max(maximum, (total - 2 * minimum + n - 3) // (n - 2))
    answer = (n * maximum - total) * cost1
    for target in {maximum, maximum + 1, boundary - 1, boundary, boundary + 1}:
        if target < maximum:
            continue
        deficit = n * target - total
        largest = target - minimum
        pairs = min(deficit // 2, deficit - largest)
        price = pairs * cost2 + (deficit - 2 * pairs) * cost1
        answer = min(answer, price)
    return answer % modulus


class Solution:
    def minCostToEqualizeArray(self, nums: list[int], cost1: int, cost2: int) -> int:
        return solve(nums, cost1, cost2)
