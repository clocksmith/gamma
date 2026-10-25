def solve(value):
    if value < 2:
        return value
    result = 0
    place = 1
    for factor in range(9, 1, -1):
        while value % factor == 0:
            value //= factor
            result += factor * place
            if result > 2147483647:
                return 0
            place *= 10
    return result if value == 1 else 0
