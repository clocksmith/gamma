"""1451. Rearrange Words in a Sentence: stably order normalized words by length then capitalize the new first word."""


def solve(text: str) -> str:
    """O(L + w log(w + 1)) time and O(L + w) auxiliary space; inputs are read-only."""
    words = text.lower().split()
    words.sort(key=len)
    sentence = ' '.join(words)
    return sentence[0].upper() + sentence[1:]


class Solution:
    def arrangeWords(self, text: str) -> str:
        return solve(text)
