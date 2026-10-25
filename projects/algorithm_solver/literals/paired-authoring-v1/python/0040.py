class Solution:
    def combinationSum2(self, candidates: list[int], target: int) -> list[list[int]]:
        ordered = sorted(candidates)
        combinations = []
        path = []

        def collect(start: int, remaining: int) -> None:
            if remaining == 0:
                combinations.append(path.copy())
                return
            for index in range(start, len(ordered)):
                if index > start and ordered[index] == ordered[index - 1]:
                    continue
                value = ordered[index]
                if value > remaining:
                    break
                path.append(value)
                collect(index + 1, remaining - value)
                path.pop()

        collect(0, target)
        return combinations
