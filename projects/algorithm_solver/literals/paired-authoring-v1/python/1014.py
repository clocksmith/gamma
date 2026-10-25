class Solution:
    def maxScoreSightseeingPair(self, values):
        best_left = values[0]
        best = values[0] + values[1] - 1
        for right in range(1, len(values)):
            best = max(best, best_left + values[right] - right)
            best_left = max(best_left, values[right] + right)
        return best
