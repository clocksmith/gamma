def solve(values):
    total = values[0]
    for index in range(1, len(values)):
        if values[index] != values[index - 1] + 1:
            break
        total += values[index]
    present = set(values)
    while total in present:
        total += 1
    return total
