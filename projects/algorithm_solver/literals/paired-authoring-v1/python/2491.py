class Solution:
    def dividePlayers(self, skill: list[int]) -> int:
        if len(skill) % 2 != 0:
            return -1
        if not skill:
            return 0
        ordered = sorted(skill)
        required = ordered[0] + ordered[-1]
        left = 0
        right = len(ordered) - 1
        chemistry = 0
        while left < right:
            if ordered[left] + ordered[right] != required:
                return -1
            chemistry += ordered[left] * ordered[right]
            left += 1
            right -= 1
        return chemistry
