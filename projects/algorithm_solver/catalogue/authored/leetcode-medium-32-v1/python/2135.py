"""2135. Count Words Obtained After Adding a Letter: remove one distinct letter from each target mask."""


def solve(startWords: list[str], targetWords: list[str]) -> int:
    """O(total characters) expected time and O(number of start words) auxiliary space; inputs are read-only."""
    def mask(word: str) -> int:
        bits = 0
        for character in word:
            bits |= 1 << (ord(character) - ord("a"))
        return bits

    starts = {mask(word) for word in startWords}
    answer = 0
    for word in targetWords:
        bits = mask(word)
        for character in word:
            without_letter = bits ^ (1 << (ord(character) - ord("a")))
            if without_letter in starts:
                answer += 1
                break
    return answer


class Solution:
    def wordCount(self, startWords: list[str], targetWords: list[str]) -> int:
        return solve(startWords, targetWords)
