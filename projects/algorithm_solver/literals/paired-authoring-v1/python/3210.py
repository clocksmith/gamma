class Solution:
    def getEncryptedString(self, s: str, k: int) -> str:
        if not s:
            return ""
        shift = k % len(s)
        return s[shift:] + s[:shift]
