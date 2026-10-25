class Solution:
    def subsetsWithDup(self, nums: list[int]) -> list[list[int]]:
        ordered = sorted(nums)
        subsets = []
        path = []

        def collect(start: int) -> None:
            subsets.append(path.copy())
            for index in range(start, len(ordered)):
                if index > start and ordered[index] == ordered[index - 1]:
                    continue
                path.append(ordered[index])
                collect(index + 1)
                path.pop()

        collect(0)
        return subsets
