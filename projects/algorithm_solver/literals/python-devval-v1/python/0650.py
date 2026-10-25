def solve(length):
    steps = 0
    divisor = 2
    while divisor * divisor <= length:
        while length % divisor == 0:
            steps += divisor
            length //= divisor
        divisor += 1
    return steps + length if length > 1 else steps
