class Solution:
    def calculateTime(self, keyboard: str, word: str) -> int:
        positions = [0] * 26
        for index, character in enumerate(keyboard):
            positions[ord(character) - ord("a")] = index
        current = 0
        time = 0
        for character in word:
            destination = positions[ord(character) - ord("a")]
            time += abs(destination - current)
            current = destination
        return time
