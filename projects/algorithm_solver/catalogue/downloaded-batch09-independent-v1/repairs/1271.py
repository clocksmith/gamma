"""Provisional decimal-string interface repair; public-definition gate remains."""
def solve(num: str) -> str:
    text = format(int(num), 'X')
    if any(c in '23456789' for c in text):
        return 'ERROR'
    return text.translate(str.maketrans('01', 'OI'))
class Solution:
    def toHexspeak(self, num: str) -> str:
        return solve(num)
