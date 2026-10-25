class Solution:
    def minDeletionSize(self, strs):
        resolved = [False] * (len(strs) - 1)
        deleted = 0
        for column in range(len(strs[0])):
            invalid = False
            for row in range(len(strs) - 1):
                if not resolved[row] and strs[row][column] > strs[row + 1][column]:
                    invalid = True
                    break
            if invalid:
                deleted += 1
                continue
            for row in range(len(strs) - 1):
                if strs[row][column] < strs[row + 1][column]:
                    resolved[row] = True
        return deleted
