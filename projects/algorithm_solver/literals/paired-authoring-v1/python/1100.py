class Solution:
    def numKLenSubstrNoRepeats(self, text, k):
        counts = {}
        total = 0
        for right, character in enumerate(text):
            counts[character] = counts.get(character, 0) + 1
            if right >= k:
                outgoing = text[right - k]
                counts[outgoing] -= 1
                if counts[outgoing] == 0:
                    del counts[outgoing]
            if right + 1 >= k and len(counts) == k:
                total += 1
        return total
