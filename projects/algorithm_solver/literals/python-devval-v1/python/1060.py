def solve(values, missing_index):
    def missing_before(index):
        return values[index] - values[0] - index

    last = len(values) - 1
    if missing_index > missing_before(last):
        return values[last] + missing_index - missing_before(last)
    low = 0
    high = len(values)
    while low < high:
        middle = (low + high) // 2
        if missing_before(middle) < missing_index:
            low = middle + 1
        else:
            high = middle
    previous = low - 1
    return values[previous] + missing_index - missing_before(previous)
