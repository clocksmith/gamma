"""214. Shortest Palindrome."""
def solve(s: str) -> str:
    combined = s + '#' + s[::-1]
    prefix = [0] * len(combined)
    for index in range(1, len(combined)):
        length = prefix[index - 1]
        while length and combined[index] != combined[length]:
            length = prefix[length - 1]
        if combined[index] == combined[length]:
            length += 1
        prefix[index] = length
    return s[prefix[-1]:][::-1] + s

class Solution:
    def shortestPalindrome(self, s: str) -> str:
        return solve(s)
