class Solution:
    def dietPlanPerformance(self, calories, k, lower, upper):
        window = 0
        score = 0
        for right, value in enumerate(calories):
            window += value
            if right >= k:
                window -= calories[right - k]
            if right + 1 >= k:
                if window < lower:
                    score -= 1
                elif window > upper:
                    score += 1
        return score
