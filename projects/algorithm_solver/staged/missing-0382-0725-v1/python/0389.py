"""389. Find the Difference. XOR character codes; inputs are preserved."""

def solve(s: str, t: str) -> str:
    value = 0
    for char in s:
        value ^= ord(char)
    for char in t:
        value ^= ord(char)
    return chr(value)


class Solution:
    def findTheDifference(self, s: str, t: str) -> str:
        return solve(s, t)
