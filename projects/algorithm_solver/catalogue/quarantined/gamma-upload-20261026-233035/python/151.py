"""151. Reverse Words in a String."""
def solve(s: str) -> str:
    return ' '.join(reversed(s.split()))

class Solution:
    def reverseWords(self, s: str) -> str:
        return solve(s)
