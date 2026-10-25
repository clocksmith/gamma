def solve(values):
    smallest = min(values)
    digit_sum = 0
    while smallest:
        smallest, digit = divmod(smallest, 10)
        digit_sum += digit
    return 1 if digit_sum % 2 == 0 else 0
