class Solution:
    def new21Game(self, n: int, k: int, maxPts: int) -> float:
        if k == 0 or n >= k - 1 + maxPts:
            return 1.0

        probabilities = [0.0] * (n + 1)
        probabilities[0] = 1.0
        window = 1.0
        answer = 0.0
        for score in range(1, n + 1):
            probabilities[score] = window / maxPts
            if score < k:
                window += probabilities[score]
            else:
                answer += probabilities[score]
            outgoing = score - maxPts
            if 0 <= outgoing < k:
                window -= probabilities[outgoing]
        return min(1.0, max(0.0, answer))
