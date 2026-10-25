class Solution:
    def removeBoxes(self, boxes: list[int]) -> int:
        memo = {}

        def score(left: int, right: int, joined: int) -> int:
            if left > right:
                return 0
            key = (left, right, joined)
            if key in memo:
                return memo[key]
            while left < right and boxes[right] == boxes[right - 1]:
                right -= 1
                joined += 1

            group = joined + 1
            best = score(left, right - 1, 0) + group * group
            for index in range(left, right):
                if boxes[index] == boxes[right]:
                    candidate = score(left, index, group) + score(index + 1, right - 1, 0)
                    best = max(best, candidate)
            memo[key] = best
            return best

        return score(0, len(boxes) - 1, 0)
