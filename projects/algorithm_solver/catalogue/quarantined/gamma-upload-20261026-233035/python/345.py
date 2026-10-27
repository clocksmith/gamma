"""345. Reverse Vowels of a String."""
def solve(s: str) -> str:
    values = list(s)
    vowels = set('aeiouAEIOU')
    left, right = 0, len(values) - 1
    while left < right:
        while left < right and values[left] not in vowels:
            left += 1
        while left < right and values[right] not in vowels:
            right -= 1
        values[left], values[right] = values[right], values[left]
        left += 1
        right -= 1
    return ''.join(values)

class Solution:
    def reverseVowels(self, s: str) -> str:
        return solve(s)
