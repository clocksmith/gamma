"""2218. Maximum Value of K Coins From Piles."""


def solve(piles: list[list[int]], k: int) -> int:
    """Multiple-choice knapsack over pile prefixes; O(k*sum(min(k,len(pile)))) time, O(k) auxiliary space. Inputs are preserved."""
    best = [float('-inf')] * (k + 1)
    best[0] = 0
    for pile in piles:
        prefix = [0]
        for coin in pile[:k]:
            prefix.append(prefix[-1] + coin)
        following = best.copy()
        for used in range(k + 1):
            if best[used] == float('-inf'):
                continue
            for count in range(1, min(len(prefix) - 1, k - used) + 1):
                following[used + count] = max(following[used + count], best[used] + prefix[count])
        best = following
    return best[k]


class Solution:
    def maxValueOfCoins(self, piles: list[list[int]], k: int) -> int:
        return solve(piles, k)
