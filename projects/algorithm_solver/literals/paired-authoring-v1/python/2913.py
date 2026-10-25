class Solution:
    def sumCounts(self, nums: list[int]) -> int:
        answer = 0
        for left in range(len(nums)):
            distinct = set()
            for right in range(left, len(nums)):
                distinct.add(nums[right])
                count = len(distinct)
                answer += count * count
        return answer
