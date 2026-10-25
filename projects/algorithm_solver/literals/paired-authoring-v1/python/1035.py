class Solution:
    def maxUncrossedLines(self, nums1, nums2):
        row = [0] * (len(nums2) + 1)
        for left in nums1:
            diagonal = 0
            for index in range(1, len(nums2) + 1):
                previous = row[index]
                if left == nums2[index - 1]:
                    row[index] = diagonal + 1
                else:
                    row[index] = max(row[index], row[index - 1])
                diagonal = previous
        return row[-1]
