class Solution:
    def numSpecialEquivGroups(self, words: list[str]) -> int:
        groups = set()
        for word in words:
            counts = [0] * 52
            for index, character in enumerate(word):
                slot = 26 * (index % 2) + ord(character) - 97
                counts[slot] += 1
            groups.add(tuple(counts))
        return len(groups)
