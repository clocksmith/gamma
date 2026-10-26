"""691. Stickers to Spell Word: memoized remaining letter counts with first-needed-letter pruning."""

from functools import lru_cache


def solve(stickers: list[str], target: str) -> int:
    """O(26 * S * C) time and O(26 * (S + C)) space; S = count states, C = stickers. Inputs are preserved."""
    needed = [0] * 26
    for character in target:
        needed[ord(character) - 97] += 1
    vectors = []
    seen = set()
    for sticker in stickers:
        counts = [0] * 26
        for character in sticker:
            index = ord(character) - 97
            counts[index] = min(needed[index], counts[index] + 1)
        vector = tuple(counts)
        if any(vector) and vector not in seen:
            seen.add(vector)
            vectors.append(vector)

    @lru_cache(maxsize=None)
    def visit(remaining):
        pivot = next((index for index, count in enumerate(remaining) if count), -1)
        if pivot < 0:
            return 0
        best = len(target) + 1
        for vector in vectors:
            if vector[pivot] == 0:
                continue
            following = tuple(max(0, count - used) for count, used in zip(remaining, vector))
            child = visit(following)
            if child >= 0:
                best = min(best, child + 1)
        return -1 if best > len(target) else best

    return visit(tuple(needed))


class Solution:
    def minStickers(self, stickers: list[str], target: str) -> int:
        return solve(stickers, target)
