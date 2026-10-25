def solve(value):
    digits = str(value)
    power = len(digits)
    return sum((ord(digit) - 48) ** power for digit in digits) == value
