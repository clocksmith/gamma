class Solution:
    def topKFrequent(self, nums: list[int], k: int) -> list[int]:
        counts = {}
        for value in nums:
            counts[value] = counts.get(value, 0) + 1

        buckets = [[] for _ in range(len(nums) + 1)]
        for value, frequency in counts.items():
            buckets[frequency].append(value)

        result = []
        for frequency in range(len(nums), 0, -1):
            for value in buckets[frequency]:
                result.append(value)
                if len(result) == k:
                    return result
        return result
