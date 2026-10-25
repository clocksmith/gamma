class Solution:
    def minOperations(self, nums: list[int]) -> int:
        parity = 0
        operations = 0
        for value in nums:
            effective = value if parity == 0 else 1 - value
            if effective == 0:
                operations += 1
                parity = 1 - parity
        return operations
