def solve(values):
    total = sum(values)
    left = 0
    for index, value in enumerate(values):
        if left == total - left - value:
            return index
        left += value
    return -1
