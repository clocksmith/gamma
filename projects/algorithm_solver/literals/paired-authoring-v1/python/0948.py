class Solution:
    def bagOfTokensScore(self, tokens, power):
        tokens.sort()
        ordered = tokens
        left = 0
        right = len(ordered) - 1
        score = 0
        best = 0
        while left <= right:
            if ordered[left] <= power:
                power -= ordered[left]
                left += 1
                score += 1
                best = max(best, score)
            elif score > 0 and left < right:
                power += ordered[right]
                right -= 1
                score -= 1
            else:
                break
        return best
