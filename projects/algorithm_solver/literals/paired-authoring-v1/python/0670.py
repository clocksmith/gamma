class Solution:
    def maximumSwap(self, num: int) -> int:
        digits = list(str(num))
        last = [-1] * 10
        for index, digit in enumerate(digits):
            last[int(digit)] = index
        for index, digit in enumerate(digits):
            for replacement in range(9, int(digit), -1):
                other = last[replacement]
                if other > index:
                    digits[index], digits[other] = digits[other], digits[index]
                    return int("".join(digits))
        return num
