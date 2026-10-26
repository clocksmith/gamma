"""917. Reverse Only Letters (Easy).

Specification: https://leetcode.com/problems/reverse-only-letters/description/
"""


def solve(s: str) -> str:
    """O(n) time and space; exchange ASCII letters while leaving nonletters at their indices."""
    result = list(s)

    def is_letter(character):
        return 'a' <= character <= 'z' or 'A' <= character <= 'Z'

    left, right = 0, len(result) - 1
    while left < right:
        if not is_letter(result[left]):
            left += 1
        elif not is_letter(result[right]):
            right -= 1
        else:
            result[left], result[right] = result[right], result[left]
            left += 1
            right -= 1
    return ''.join(result)


class Solution:
    def reverseOnlyLetters(self, s: str) -> str:
        return solve(s)
