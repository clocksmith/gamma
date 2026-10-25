def contains_text(text: str, pattern: str) -> bool:
    for start in range(len(text) - len(pattern) + 1):
        offset = 0
        while offset < len(pattern) and text[start + offset] == pattern[offset]:
            offset += 1
        if offset == len(pattern):
            return True
    return False


class Solution:
    def numOfStrings(self, patterns: list[str], word: str) -> int:
        count = 0
        for pattern in patterns:
            if contains_text(word, pattern):
                count += 1
        return count
