"""2489. Number of Substrings With Fixed Ratio: count equal zero/one weighted prefix balances."""


def solve(s: str, num1: int, num2: int) -> int:
    """O(n) expected time and O(n) auxiliary space on the stated integer domain; inputs are read-only."""
    frequencies = {0: 1}
    balance = answer = 0
    for char in s:
        balance += num2 if char == '0' else -num1
        answer += frequencies.get(balance, 0)
        frequencies[balance] = frequencies.get(balance, 0) + 1
    return answer


class Solution:
    def fixedRatio(self, s: str, num1: int, num2: int) -> int:
        return solve(s, num1, num2)
