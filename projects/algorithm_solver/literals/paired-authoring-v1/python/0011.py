class Solution:
    def maxArea(self, height: list[int]) -> int:
        left = 0
        right = len(height) - 1
        best = 0
        while left < right:
            area = (right - left) * min(height[left], height[right])
            best = max(best, area)
            # No narrower pair using the shorter endpoint can beat this area.
            # Thus any pair improving best remains inside the next interval.
            if height[left] <= height[right]:
                left += 1
            else:
                right -= 1
        return best
