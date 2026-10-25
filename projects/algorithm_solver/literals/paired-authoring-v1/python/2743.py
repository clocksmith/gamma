class Solution:
    def numberOfSpecialSubstrings(self, text):
        last_seen = {}
        left = 0
        total = 0
        for right, character in enumerate(text):
            left = max(left, last_seen.get(character, -1) + 1)
            last_seen[character] = right
            total += right - left + 1
        return total
