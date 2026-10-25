class Solution:
    def countSubstrings(self, s: str) -> int:
        count = 0
        for center in range(len(s)):
            for offset in range(2):
                left = center
                right = center + offset
                while left >= 0 and right < len(s) and s[left] == s[right]:
                    count += 1
                    left -= 1
                    right += 1
        return count
