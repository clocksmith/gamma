class Solution:
    def maximumTripletValue(self, nums: list[int]) -> int:
        largest = nums[0]
        difference = 0
        answer = 0
        for index in range(1, len(nums)):
            value = nums[index]
            answer = max(answer, difference * value)
            difference = max(difference, largest - value)
            largest = max(largest, value)
        return answer
