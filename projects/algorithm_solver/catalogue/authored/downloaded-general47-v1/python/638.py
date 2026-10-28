"""638. Shopping Offers (Medium).

Specification: https://leetcode.com/problems/shopping-offers/description/
"""


def solve(price: list[int], special: list[list[int]], needs: list[int]) -> int:
    memo = {}

    def dfs(current):
        key = tuple(current)
        if key in memo:
            return memo[key]
        best = sum(current[i] * price[i] for i in range(len(current)))
        for offer in special:
            nxt = current[:]
            valid = True
            for i in range(len(current)):
                nxt[i] -= offer[i]
                if nxt[i] < 0:
                    valid = False
                    break
            if valid:
                best = min(best, offer[-1] + dfs(nxt))
        memo[key] = best
        return best

    return dfs(needs[:])


class Solution:
    def shoppingOffers(self, price: list[int], special: list[list[int]], needs: list[int]) -> int:
        return solve(price, special, needs)
