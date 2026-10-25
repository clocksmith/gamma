class Solution:
    def subsets(self, nums: list[int]) -> list[list[int]]:
        subsets = []
        path = []

        def collect(start: int) -> None:
            subsets.append(path.copy())
            for index in range(start, len(nums)):
                path.append(nums[index])
                collect(index + 1)
                path.pop()

        collect(0)
        return subsets
