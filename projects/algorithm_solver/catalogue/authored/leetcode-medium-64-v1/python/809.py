"""809. Expressive Words: match letter runs against the allowed stretched groups."""


def solve(s: str, words: list[str]) -> int:
    """O(|s| + sum(|word|)) time and O(|s|) auxiliary space; inputs are read-only."""
    groups = []
    index = 0
    while index < len(s):
        end = index + 1
        while end < len(s) and s[end] == s[index]:
            end += 1
        groups.append((s[index], end - index))
        index = end
    answer = 0
    for word in words:
        position = 0
        valid = True
        for character, required in groups:
            if position == len(word) or word[position] != character:
                valid = False
                break
            end = position + 1
            while end < len(word) and word[end] == character:
                end += 1
            actual = end - position
            if actual > required or (actual != required and required < 3):
                valid = False
                break
            position = end
        if valid and position == len(word):
            answer += 1
    return answer


class Solution:
    def expressiveWords(self, s: str, words: list[str]) -> int:
        return solve(s, words)
