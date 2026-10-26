"""1842. Next Palindrome Using Same Digits.

Next-permute the left half and mirror it, preserving the center; O(n) time and space.
"""

def solve(num: str) -> str:
    half = len(num) // 2
    digits = list(num[:half])
    pivot = half - 2
    while pivot >= 0 and digits[pivot] >= digits[pivot + 1]:
        pivot -= 1
    if pivot < 0:
        return ''
    successor = half - 1
    while digits[successor] <= digits[pivot]:
        successor -= 1
    digits[pivot], digits[successor] = digits[successor], digits[pivot]
    digits[pivot + 1:] = reversed(digits[pivot + 1:])
    left = ''.join(digits)
    middle = num[half] if len(num) % 2 else ''
    return left + middle + left[::-1]


class Solution:
    def nextPalindrome(self, num: str) -> str:
        return solve(num)
