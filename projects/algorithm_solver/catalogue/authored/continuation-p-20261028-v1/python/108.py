class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sortedArrayToBST(self, nums):
        def build(lo, hi):
            if lo >= hi:
                return None
            middle = (lo + hi) // 2
            return TreeNode(nums[middle], build(lo, middle), build(middle + 1, hi))
        return build(0, len(nums))
