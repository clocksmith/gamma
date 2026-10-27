"""488. Zuma Game. Memoized insertion search includes both matching insertions and splitting an equal-color pair."""

from functools import lru_cache

def solve(board: str, hand: str) -> int:
    colors = 'RYBGW'
    initial = tuple(hand.count(color) for color in colors)
    def shrink(text):
        while True:
            pieces = []
            changed = False
            i = 0
            while i < len(text):
                j = i + 1
                while j < len(text) and text[j] == text[i]:
                    j += 1
                if j - i < 3:
                    pieces.append(text[i:j])
                else:
                    changed = True
                i = j
            text = ''.join(pieces)
            if not changed:
                return text
    @lru_cache(None)
    def search(text, counts):
        if not text:
            return 0
        for i, color in enumerate(colors):
            if color in text and text.count(color) + counts[i] < 3:
                return 6
        best = 6
        for c, color in enumerate(colors):
            if counts[c] == 0:
                continue
            next_counts = list(counts)
            next_counts[c] -= 1
            next_counts = tuple(next_counts)
            generated = set()
            for position in range(len(text) + 1):
                if position and text[position - 1] == color:
                    continue
                matches = position < len(text) and text[position] == color
                splits = 0 < position < len(text) and text[position - 1] == text[position] and text[position] != color
                if not matches and not splits:
                    continue
                following = shrink(text[:position] + color + text[position:])
                if following in generated:
                    continue
                generated.add(following)
                best = min(best, 1 + search(following, next_counts))
        return best
    answer = search(shrink(board), initial)
    return answer if answer <= len(hand) else -1


class Solution:
    def findMinStep(self, board: str, hand: str) -> int:
        return solve(board, hand)
