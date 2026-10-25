def sorted_k_sum(nums: list[int], target: int, arity: int) -> list[list[int]]:
    values = sorted(nums)
    count = len(values)
    result = []
    prefix = []

    def search(start: int, remaining: int, residual: int) -> None:
        if remaining == 2:
            left = start
            right = count - 1
            while left < right:
                pair_sum = values[left] + values[right]
                if pair_sum < residual:
                    left += 1
                elif pair_sum > residual:
                    right -= 1
                else:
                    result.append(prefix + [values[left], values[right]])
                    left += 1
                    right -= 1
                    while left < right and values[left] == values[left - 1]:
                        left += 1
                    while left < right and values[right] == values[right + 1]:
                        right -= 1
            return

        # Ascending, distinct choices preserve lexicographic tuple order.
        for index in range(start, count - remaining + 1):
            if index > start and values[index] == values[index - 1]:
                continue
            prefix.append(values[index])
            search(index + 1, remaining - 1, residual - values[index])
            prefix.pop()

    search(0, arity, target)
    return result


class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        return sorted_k_sum(nums, 0, 3)
