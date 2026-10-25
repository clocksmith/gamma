def upper_bound(values: list[int], target: int) -> int:
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
    def makeArrayIncreasing(self, arr1: list[int], arr2: list[int]) -> int:
        replacements = sorted(set(arr2))
        states = {-1: 0}
        for value in arr1:
            following = {}
            for previous, cost in states.items():
                if value > previous:
                    following[value] = min(following.get(value, len(arr1) + 1), cost)
                index = upper_bound(replacements, previous)
                if index < len(replacements):
                    replacement = replacements[index]
                    following[replacement] = min(following.get(replacement, len(arr1) + 1), cost + 1)
            if not following:
                return -1
            states = following
        return min(states.values())
