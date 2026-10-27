"""638. Shopping Offers."""

from functools import lru_cache

def solve(price: list[int], special: list[list[int]], needs: list[int]) -> int:
    size = len(price)
    offers = [offer[:] for offer in special if any(offer[:size])
              and all(offer[i] <= needs[i] for i in range(size))
              and offer[-1] < sum(offer[i] * price[i] for i in range(size))]
    @lru_cache(None)
    def cost(remaining):
        best = sum(remaining[i] * price[i] for i in range(size))
        for offer in offers:
            if all(offer[i] <= remaining[i] for i in range(size)):
                following = tuple(remaining[i] - offer[i] for i in range(size))
                best = min(best, offer[-1] + cost(following))
        return best
    return cost(tuple(needs))


class Solution:
    def shoppingOffers(self, price: list[int], special: list[list[int]], needs: list[int]) -> int:
        return solve(price, special, needs)
