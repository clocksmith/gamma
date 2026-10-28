"""299. Bulls and Cows (Medium).

Specification: https://leetcode.com/problems/bulls-and-cows/description/
"""


def solve(secret: str, guess: str) -> str:
    bulls = 0
    secret_counts = [0] * 10
    guess_counts = [0] * 10
    for i in range(len(secret)):
        if secret[i] == guess[i]:
            bulls += 1
        else:
            secret_counts[int(secret[i])] += 1
            guess_counts[int(guess[i])] += 1
    cows = sum(min(secret_counts[d], guess_counts[d]) for d in range(10))
    return f"{bulls}A{cows}B"


class Solution:
    def getHint(self, secret: str, guess: str) -> str:
        return solve(secret, guess)
