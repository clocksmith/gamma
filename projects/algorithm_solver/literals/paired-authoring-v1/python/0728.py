def is_self_dividing(value: int) -> bool:
    remaining = value
    while remaining > 0:
        digit = remaining % 10
        if digit == 0 or value % digit != 0:
            return False
        remaining //= 10
    return True


class Solution:
    def selfDividingNumbers(self, left: int, right: int) -> list[int]:
        result = []
        for value in range(left, right + 1):
            if is_self_dividing(value):
                result.append(value)
        return result
