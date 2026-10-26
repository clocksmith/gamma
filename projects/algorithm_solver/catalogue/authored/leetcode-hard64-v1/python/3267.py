"""3267. Count Almost Equal Pairs II: enumerate up to two digit swaps and count earlier values."""


def solve(nums: list[int]) -> int:
    """O(n log n + n*d^4) expected time and O(n + d^4) auxiliary space, d<=7. Inputs are preserved."""
    frequency = {}
    answer = 0
    for number in sorted(nums):
        digits = [int(character) for character in str(number)]
        width = len(digits)
        powers = [10 ** (width - index - 1) for index in range(width)]
        variants = {number}
        for left in range(width):
            for right in range(left + 1, width):
                if digits[left] == digits[right]:
                    continue
                first = number + (digits[right] - digits[left]) * (powers[left] - powers[right])
                variants.add(first)
                digits[left], digits[right] = digits[right], digits[left]
                for second_left in range(width):
                    for second_right in range(second_left + 1, width):
                        second = first + (digits[second_right] - digits[second_left]) * (powers[second_left] - powers[second_right])
                        variants.add(second)
                digits[left], digits[right] = digits[right], digits[left]
        answer += sum(frequency.get(value, 0) for value in variants)
        frequency[number] = frequency.get(number, 0) + 1
    return answer


class Solution:
    def countPairs(self, nums: list[int]) -> int:
        return solve(nums)
