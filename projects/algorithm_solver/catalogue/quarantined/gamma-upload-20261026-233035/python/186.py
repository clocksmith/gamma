"""186. Reverse Words in a String II."""
def solve(s: list[str]) -> None:
    s.reverse()
    start = 0
    for end in range(len(s) + 1):
        if end == len(s) or s[end] == ' ':
            s[start:end] = reversed(s[start:end])
            start = end + 1

class Solution:
    def reverseWords(self, s: list[str]) -> None:
        solve(s)
