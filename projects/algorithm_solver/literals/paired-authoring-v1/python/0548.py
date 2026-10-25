class Solution:
    def splitArray(self, nums: list[int]) -> bool:
        if len(nums) < 7:
            return False

        prefix = [0]
        for value in nums:
            prefix.append(prefix[-1] + value)
        for middle in range(3, len(nums) - 3):
            sums = set()
            for left in range(1, middle - 1):
                first = prefix[left]
                second = prefix[middle] - prefix[left + 1]
                if first == second:
                    sums.add(first)
            for right in range(middle + 2, len(nums) - 1):
                third = prefix[right] - prefix[middle + 1]
                fourth = prefix[len(nums)] - prefix[right + 1]
                if third == fourth and third in sums:
                    return True
        return False
