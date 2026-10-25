class Solution:
    def findPairs(self, nums: list[int], k: int) -> int:
        if k < 0:
            return 0

        counts = {}
        for value in nums:
            counts[value] = counts.get(value, 0) + 1
        pairs = 0
        for value, count in counts.items():
            if k == 0:
                if count > 1:
                    pairs += 1
            elif value + k in counts:
                pairs += 1
        return pairs
