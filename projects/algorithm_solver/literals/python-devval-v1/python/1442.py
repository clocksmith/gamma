def solve(values):
    counts = {0: 1}
    positions = {0: 0}
    prefix = 0
    triples = 0
    for end, value in enumerate(values, 1):
        prefix ^= value
        triples += counts.get(prefix, 0) * (end - 1) - positions.get(prefix, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
        positions[prefix] = positions.get(prefix, 0) + end
    return triples
