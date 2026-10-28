def solve(technique1, technique2, k):
    gains = sorted((a - b for a, b in zip(technique1, technique2)), reverse=True)
    return sum(technique2) + sum(x for i, x in enumerate(gains) if i < k or x > 0)


class Solution:
    def maxPoints(self, technique1, technique2, k):
        return solve(technique1, technique2, k)
