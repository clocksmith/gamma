def solve(first, second):
    previous = [None] * (len(second) + 1)
    for left in first:
        current = [None] * (len(second) + 1)
        for column, right in enumerate(second, 1):
            product = left * right
            best = product
            if previous[column - 1] is not None:
                best = max(best, product + previous[column - 1])
            if previous[column] is not None:
                best = max(best, previous[column])
            if current[column - 1] is not None:
                best = max(best, current[column - 1])
            current[column] = best
        previous = current
    return previous[-1]
