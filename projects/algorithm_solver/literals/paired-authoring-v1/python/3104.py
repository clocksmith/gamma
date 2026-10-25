class Solution:
    def maxSubstringLength(self, text):
        first = {}
        last = {}
        for index, character in enumerate(text):
            if character not in first:
                first[character] = index
            last[character] = index
        best = -1
        for left in first.values():
            required_end = left
            for right in range(left, len(text)):
                character = text[right]
                if first[character] < left:
                    break
                required_end = max(required_end, last[character])
                if right == required_end and right - left + 1 < len(text):
                    best = max(best, right - left + 1)
        return best
