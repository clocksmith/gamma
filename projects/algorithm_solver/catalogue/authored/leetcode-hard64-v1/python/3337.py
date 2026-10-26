"""3337. Total Characters in String After Transformations II: exponentiate the 26-letter transition matrix."""


def solve(s: str, t: int, nums: list[int]) -> int:
    """O(|s| + 26^3 log(t+1)) time and O(26^2) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    matrix = [[0] * 26 for _ in range(26)]
    for letter, count in enumerate(nums):
        for offset in range(1, count + 1):
            matrix[letter][(letter + offset) % 26] += 1
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1

    def multiply(first, second):
        product = [[0] * 26 for _ in range(26)]
        for row in range(26):
            for middle in range(26):
                if first[row][middle] == 0:
                    continue
                for column in range(26):
                    product[row][column] = (product[row][column] + first[row][middle] * second[middle][column]) % modulus
        return product

    exponent = t
    while exponent:
        if exponent & 1:
            following = [0] * 26
            for row in range(26):
                for column in range(26):
                    following[column] = (following[column] + counts[row] * matrix[row][column]) % modulus
            counts = following
        exponent //= 2
        if exponent:
            matrix = multiply(matrix, matrix)
    return sum(counts) % modulus


class Solution:
    def lengthAfterTransformations(self, s: str, t: int, nums: list[int]) -> int:
        return solve(s, t, nums)
