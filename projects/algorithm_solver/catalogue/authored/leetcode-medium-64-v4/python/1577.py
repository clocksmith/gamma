"""1577. Number of Ways Where Square of Number Is Equal to Product of Two Numbers: count matching products with duplicate-aware two-pointer scans."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n * m + n log(n + 1) + m log(m + 1)) time and O(n + m) auxiliary space; inputs are read-only."""
    first, second = sorted(nums1), sorted(nums2)

    def count(squares: list[int], values: list[int]) -> int:
        total = 0
        for value in squares:
            target = value * value
            left, right = 0, len(values) - 1
            while left < right:
                product = values[left] * values[right]
                if product < target:
                    left += 1
                elif product > target:
                    right -= 1
                elif values[left] == values[right]:
                    width = right - left + 1
                    total += width * (width - 1) // 2
                    break
                else:
                    low, high = values[left], values[right]
                    low_count = high_count = 0
                    while left <= right and values[left] == low:
                        low_count += 1
                        left += 1
                    while left <= right and values[right] == high:
                        high_count += 1
                        right -= 1
                    total += low_count * high_count
        return total

    return count(first, second) + count(second, first)


class Solution:
    def numTriplets(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
