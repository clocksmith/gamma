"""1449. Form Largest Integer With Digits That Add up to Target: maximize digit count, then reconstruct in descending digit order; O(9*target) time and O(target) space."""


def solve(cost: list[int], target: int) -> str:
    digits = [-1] * (target + 1)
    digits[0] = 0
    for amount in range(1, target + 1):
        for price in cost:
            if amount >= price and digits[amount - price] >= 0:
                digits[amount] = max(digits[amount], digits[amount - price] + 1)
    if digits[target] < 0:
        return '0'
    answer = []
    amount = target
    for digit in range(9, 0, -1):
        price = cost[digit - 1]
        while amount >= price and digits[amount] == digits[amount - price] + 1:
            answer.append(str(digit))
            amount -= price
    return ''.join(answer)


class Solution:
    def largestNumber(self, cost: list[int], target: int) -> str:
        return solve(cost, target)
