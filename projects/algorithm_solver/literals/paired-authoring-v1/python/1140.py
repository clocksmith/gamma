class Solution:
    def stoneGameII(self, piles: list[int]) -> int:
        size = len(piles)
        if size == 0:
            return 0
        suffix = [0] * (size + 1)
        for index in range(size - 1, -1, -1):
            suffix[index] = suffix[index + 1] + piles[index]
        scores = [[0] * (size + 1) for _ in range(size + 1)]
        for index in range(size - 1, -1, -1):
            for limit in range(1, size + 1):
                if index + 2 * limit >= size:
                    scores[index][limit] = suffix[index]
                else:
                    best = 0
                    for taken in range(1, 2 * limit + 1):
                        opponent = scores[index + taken][max(limit, taken)]
                        best = max(best, suffix[index] - opponent)
                    scores[index][limit] = best
        return scores[0][1]
