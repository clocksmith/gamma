class Solution:
    def prefixesDivBy5(self, nums):
        answer = []
        remainder = 0
        for bit in nums:
            remainder = (remainder * 2 + bit) % 5
            answer.append(remainder == 0)
        return answer
