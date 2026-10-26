"""68. Text Justification: greedy line packing with left-biased extra spaces."""


def solve(words: list[str], maxWidth: int) -> list[str]:
    """O(N + W) time and O(W) output space, W = output characters. Inputs are preserved."""
    lines = []
    left = 0
    while left < len(words):
        right = left
        letters = 0
        while right < len(words) and letters + len(words[right]) + right - left <= maxWidth:
            letters += len(words[right])
            right += 1
        gaps = right - left - 1
        if right == len(words) or gaps == 0:
            lines.append(' '.join(words[left:right]).ljust(maxWidth))
        else:
            width, extra = divmod(maxWidth - letters, gaps)
            pieces = []
            for index in range(left, right):
                pieces.append(words[index])
                if index + 1 < right:
                    pieces.append(' ' * (width + (index - left < extra)))
            lines.append(''.join(pieces))
        left = right
    return lines


class Solution:
    def fullJustify(self, words: list[str], maxWidth: int) -> list[str]:
        return solve(words, maxWidth)
