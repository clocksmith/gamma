def solve(value):
    sign = -1 if value < 0 else 1
    remaining = abs(value)
    reversed_value = 0
    while remaining:
        remaining, digit = divmod(remaining, 10)
        reversed_value = reversed_value * 10 + digit
    reversed_value *= sign
    if -(1 << 31) <= reversed_value < (1 << 31):
        return reversed_value
    return 0
