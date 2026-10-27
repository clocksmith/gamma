"""291. Word Pattern II."""
def solve(pattern: str, s: str) -> bool:
    mapping = {}
    used = set()
    def visit(pattern_index: int, text_index: int) -> bool:
        if pattern_index == len(pattern):
            return text_index == len(s)
        char = pattern[pattern_index]
        if char in mapping:
            word = mapping[char]
            return s.startswith(word, text_index) and visit(pattern_index + 1, text_index + len(word))
        remaining = len(pattern) - pattern_index - 1
        for end in range(text_index + 1, len(s) - remaining + 1):
            word = s[text_index:end]
            if word in used:
                continue
            mapping[char] = word
            used.add(word)
            if visit(pattern_index + 1, end):
                return True
            used.remove(word)
            del mapping[char]
        return False
    return visit(0, 0)

class Solution:
    def wordPatternMatch(self, pattern: str, s: str) -> bool:
        return solve(pattern, s)
