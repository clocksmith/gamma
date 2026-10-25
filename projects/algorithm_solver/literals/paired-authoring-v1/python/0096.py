class Solution:
    def numTrees(self, n: int) -> int:
        counts = [0] * (n + 1)
        counts[0] = 1
        for size in range(1, n + 1):
            for left_size in range(size):
                right_size = size - left_size - 1
                counts[size] += counts[left_size] * counts[right_size]
        return counts[n]
