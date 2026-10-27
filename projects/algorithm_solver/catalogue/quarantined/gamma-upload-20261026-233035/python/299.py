"""299. Bulls and Cows."""
from collections import Counter

def solve(secret: str, guess: str) -> str:
    bulls = sum(left == right for left, right in zip(secret, guess))
    shared = sum((Counter(secret) & Counter(guess)).values())
    return f'{bulls}A{shared - bulls}B'

class Solution:
    def getHint(self, secret: str, guess: str) -> str:
        return solve(secret, guess)
