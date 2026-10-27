"""287. Find the Duplicate Number."""
def solve(nums: list[int]) -> int:
    slow = fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow

class Solution:
    def findDuplicate(self, nums: list[int]) -> int:
        return solve(nums)
