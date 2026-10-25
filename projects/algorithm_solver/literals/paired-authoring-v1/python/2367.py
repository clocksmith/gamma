class Solution:
    def arithmeticTriplets(self, nums: list[int], diff: int) -> int:
        seen = set()
        count = 0
        for value in nums:
            if value - diff in seen and value - 2 * diff in seen:
                count += 1
            seen.add(value)
        return count
