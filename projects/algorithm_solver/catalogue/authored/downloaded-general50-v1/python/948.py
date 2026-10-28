"""948. Bag of Tokens (Medium).

Specification: https://leetcode.com/problems/bag-of-tokens/description/
"""


def solve(tokens: list[int], power: int) -> int:
    ordered = sorted(tokens)
    left, right = 0, len(ordered) - 1
    score = 0
    best = 0
    while left <= right:
        if power >= ordered[left]:
            power -= ordered[left]
            left += 1
            score += 1
            best = max(best, score)
        elif score > 0:
            power += ordered[right]
            right -= 1
            score -= 1
        else:
            break
    return best


class Solution:
    def bagOfTokensScore(self, tokens: list[int], power: int) -> int:
        return solve(tokens, power)
