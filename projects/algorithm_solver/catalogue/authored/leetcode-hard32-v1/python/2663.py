"""2663. Lexicographically Smallest Beautiful String."""

def solve(s: str, k: int) -> str:
    """O(n*k) time, O(n) space; avoid equal characters one or two positions apart."""
    letters = [ord(char) - 97 for char in s]
    for index in range(len(letters) - 1, -1, -1):
        for candidate in range(letters[index] + 1, k):
            if index >= 1 and candidate == letters[index - 1]:
                continue
            if index >= 2 and candidate == letters[index - 2]:
                continue
            letters[index] = candidate
            # k >= 4 ensures a legal smallest letter for every suffix position.
            for following in range(index + 1, len(letters)):
                candidate = 0
                while (candidate == letters[following - 1]
                       or following >= 2 and candidate == letters[following - 2]):
                    candidate += 1
                letters[following] = candidate
            return ''.join(chr(97 + letter) for letter in letters)
    return ''


class Solution:
    def smallestBeautifulString(self, s: str, k: int) -> str:
        return solve(s, k)
