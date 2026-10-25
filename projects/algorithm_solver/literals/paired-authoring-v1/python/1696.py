class Solution:
    def maxResult(self, nums: list[int], k: int) -> int:
        queue = [(0, nums[0])]
        head = 0
        score = nums[0]
        for index in range(1, len(nums)):
            while queue[head][0] < index - k:
                head += 1
            score = queue[head][1] + nums[index]
            while len(queue) > head and queue[-1][1] <= score:
                queue.pop()
            queue.append((index, score))
        return score
