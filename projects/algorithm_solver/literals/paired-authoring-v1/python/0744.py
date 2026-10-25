def upper_bound(values: list[str], target: str) -> int:
    left = 0
    right = len(values)
    while left < right:
        middle = left + (right - left) // 2
        if values[middle] <= target:
            left = middle + 1
        else:
            right = middle
    return left


class Solution:
    def nextGreatestLetter(self, letters: list[str], target: str) -> str:
        index = upper_bound(letters, target)
        if index == len(letters):
            index = 0
        return letters[index]
