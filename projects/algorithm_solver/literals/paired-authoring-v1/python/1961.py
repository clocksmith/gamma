class Solution:
    def isPrefixString(self, s: str, words: list[str]) -> bool:
        offset = 0
        for word in words:
            if not s.startswith(word, offset):
                return False
            offset += len(word)
            if offset == len(s):
                return True
        return False
