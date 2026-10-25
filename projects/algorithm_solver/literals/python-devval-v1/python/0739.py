def solve(temperatures):
    result = [0] * len(temperatures)
    unresolved = []
    for day, temperature in enumerate(temperatures):
        while unresolved and temperatures[unresolved[-1]] < temperature:
            previous = unresolved.pop()
            result[previous] = day - previous
        unresolved.append(day)
    return result
