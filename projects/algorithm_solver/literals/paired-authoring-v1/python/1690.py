class Solution:
    def stoneGameVII(self, stones: list[int]) -> int:
        size = len(stones)
        if size == 0:
            return 0
        prefix = [0]
        for value in stones:
            prefix.append(prefix[-1] + value)
        scores = [0] * size
        for length in range(2, size + 1):
            for left in range(size - length + 1):
                right = left + length - 1
                remove_left = prefix[right + 1] - prefix[left + 1] - scores[left + 1]
                remove_right = prefix[right] - prefix[left] - scores[left]
                scores[left] = max(remove_left, remove_right)
        return scores[0]
