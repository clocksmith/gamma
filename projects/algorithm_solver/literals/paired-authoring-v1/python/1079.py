def count_sequences(counts: list[int]) -> int:
    total = 0
    for letter in range(26):
        if counts[letter] > 0:
            counts[letter] -= 1
            total += 1 + count_sequences(counts)
            counts[letter] += 1
    return total


class Solution:
    def numTilePossibilities(self, tiles: str) -> int:
        counts = [0] * 26
        for letter in tiles:
            counts[ord(letter) - ord("A")] += 1
        return count_sequences(counts)
