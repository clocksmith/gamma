class Solution:
    def minimumRecolors(self, blocks: str, k: int) -> int:
        white = 0
        best = k
        for index, color in enumerate(blocks):
            if color == "W":
                white += 1
            if index >= k and blocks[index - k] == "W":
                white -= 1
            if index + 1 >= k:
                best = min(best, white)
        return best
