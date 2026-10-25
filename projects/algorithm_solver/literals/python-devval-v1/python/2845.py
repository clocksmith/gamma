def solve(values, modulo, remainder):
    counts = {0: 1}
    prefix = 0
    answer = 0
    for value in values:
        if value % modulo == remainder:
            prefix = (prefix + 1) % modulo
        answer += counts.get((prefix - remainder) % modulo, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return answer
