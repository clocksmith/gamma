"""13. Roman to Integer."""
def solve(s: str) -> int:
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    for index, char in enumerate(s):
        value = values[char]
        total += -value if index + 1 < len(s) and value < values[s[index + 1]] else value
    return total

class Solution:
    def romanToInt(self, s: str) -> int:
        return solve(s)
