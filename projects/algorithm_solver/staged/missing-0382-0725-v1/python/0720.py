"""720. Longest Word in Dictionary."""

def solve(words: list[str]) -> str:
    built = {''}
    answer = ''
    for word in sorted(words):
        if word[:-1] in built:
            built.add(word)
            if len(word) > len(answer):
                answer = word
    return answer


class Solution:
    def longestWord(self, words: list[str]) -> str:
        return solve(words)
