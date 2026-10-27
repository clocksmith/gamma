"""241. Different Ways to Add Parentheses."""
from functools import lru_cache

def solve(expression: str) -> list[int]:
    @lru_cache(None)
    def compute(text: str):
        result = []
        for index, char in enumerate(text):
            if char in '+-*':
                for left in compute(text[:index]):
                    for right in compute(text[index + 1:]):
                        result.append(left + right if char == '+' else left - right if char == '-' else left * right)
        return tuple(result) if result else (int(text),)
    return list(compute(expression))

class Solution:
    def diffWaysToCompute(self, expression: str) -> list[int]:
        return solve(expression)
