"""500. Keyboard Row."""

def solve(words: list[str]) -> list[str]:
    row = {char: index for index, letters in enumerate(('qwertyuiop', 'asdfghjkl', 'zxcvbnm')) for char in letters}
    return [word for word in words if len({row[char] for char in word.lower()}) <= 1]


class Solution:
    def findWords(self, words: list[str]) -> list[str]:
        return solve(words)
