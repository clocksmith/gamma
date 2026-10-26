"""1108. Defanging an IP Address (Easy).

Specification: https://leetcode.com/problems/defanging-an-ip-address/description/
"""


def solve(address: str) -> str:
    """O(n) time and space; replace every period in the valid input address."""
    return address.replace('.', '[.]')


class Solution:
    def defangIPaddr(self, address: str) -> str:
        return solve(address)
