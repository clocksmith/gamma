"""524. Longest Word in Dictionary through Deleting."""

def solve(s: str, dictionary: list[str]) -> str:
    for word in sorted(dictionary, key=lambda word: (-len(word), word)):
        index = 0
        for char in s:
            if index < len(word) and char == word[index]:
                index += 1
        if index == len(word):
            return word
    return ''


class Solution:
    def findLongestWord(self, s: str, dictionary: list[str]) -> str:
        return solve(s, dictionary)
