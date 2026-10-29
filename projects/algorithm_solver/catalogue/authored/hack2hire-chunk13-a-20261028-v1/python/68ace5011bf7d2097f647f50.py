"""Hack2Hire 68ace5011bf7d2097f647f50 (Palindrome Check with Ignore Set) over an INFERRED spec; qualification unknown."""


def solve(ignoreArray, inputArray):
    ignore = set(ignoreArray)
    left, right = 0, len(inputArray) - 1
    while left < right:
        if inputArray[left] in ignore:
            left += 1
        elif inputArray[right] in ignore:
            right -= 1
        elif inputArray[left] != inputArray[right]:
            return False
        else:
            left += 1
            right -= 1
    return True


class Solution:
    def isPalindromeIgnoring(self, ignoreArray, inputArray):
        return solve(ignoreArray, inputArray)
