class Solution:
    def minimumSeconds(self, nums: list[int]) -> int:
        positions = {}
        for index, value in enumerate(nums):
            if value not in positions:
                positions[value] = []
            positions[value].append(index)
        answer = len(nums)
        for indices in positions.values():
            gap = indices[0] + len(nums) - indices[-1]
            for index in range(1, len(indices)):
                gap = max(gap, indices[index] - indices[index - 1])
            answer = min(answer, gap // 2)
        return answer
