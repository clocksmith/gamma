"""318. Maximum Product of Word Lengths."""
def solve(words: list[str]) -> int:
    masks = {}
    for word in words:
        mask = 0
        for char in word:
            mask |= 1 << (ord(char) - 97)
        masks[mask] = max(masks.get(mask, 0), len(word))
    items = list(masks.items())
    return max((left_length * right_length for index, (left_mask, left_length) in enumerate(items)
                for right_mask, right_length in items[index + 1:] if not left_mask & right_mask), default=0)

class Solution:
    def maxProduct(self, words: list[str]) -> int:
        return solve(words)
