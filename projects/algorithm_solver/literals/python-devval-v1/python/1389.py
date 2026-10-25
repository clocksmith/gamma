def solve(values, indices):
    result = []
    for value, index in zip(values, indices):
        result.insert(index, value)
    return result
