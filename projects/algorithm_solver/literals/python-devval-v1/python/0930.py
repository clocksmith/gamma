def solve(values, target):
    frequencies = {0: 1}
    prefix = 0
    result = 0
    for value in values:
        prefix += value
        result += frequencies.get(prefix - target, 0)
        frequencies[prefix] = frequencies.get(prefix, 0) + 1
    return result
