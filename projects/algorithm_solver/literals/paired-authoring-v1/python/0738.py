class Solution:
    def monotoneIncreasingDigits(self, n: int) -> int:
        digits = list(str(n))
        boundary = len(digits)
        for index in range(len(digits) - 1, 0, -1):
            if digits[index - 1] > digits[index]:
                digits[index - 1] = str(int(digits[index - 1]) - 1)
                boundary = index
        for index in range(boundary, len(digits)):
            digits[index] = "9"
        return int("".join(digits))
