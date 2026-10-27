"""656. Coin Path. Suffix minimum costs choose the smallest next index on ties."""

def solve(coins: list[int], maxJump: int) -> list[int]:
    n = len(coins)
    if n == 0 or coins[0] == -1 or coins[-1] == -1:
        return []
    cost = [float('inf')] * n
    following = [-1] * n
    cost[-1] = coins[-1]
    for i in range(n - 2, -1, -1):
        if coins[i] == -1:
            continue
        for j in range(i + 1, min(n, i + maxJump + 1)):
            candidate = coins[i] + cost[j]
            if candidate < cost[i]:
                cost[i], following[i] = candidate, j
    if cost[0] == float('inf'):
        return []
    answer = []
    index = 0
    while index != -1:
        answer.append(index + 1)
        index = following[index]
    return answer


class Solution:
    def cheapestJump(self, coins: list[int], maxJump: int) -> list[int]:
        return solve(coins, maxJump)
