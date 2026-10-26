"""1359. Count All Valid Pickup and Delivery Options: insert each pickup/delivery pair; O(n) time and O(1) space."""


def solve(n: int) -> int:
    modulus = 1_000_000_007
    ways = 1
    for count in range(1, n + 1):
        ways = ways * count % modulus
        ways = ways * (2 * count - 1) % modulus
    return ways


class Solution:
    def countOrders(self, n: int) -> int:
        return solve(n)
