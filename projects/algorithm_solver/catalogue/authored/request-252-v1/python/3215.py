# Original candidate; contract and evidence: ../batch1/manifest.json
def solve(a, b, c):
    counts = []
    for values in (a, b, c):
        odd = sum(value.bit_count() % 2 for value in values)
        counts.append((len(values) - odd, odd))
    return sum(counts[0][i] * counts[1][j] * counts[2][i ^ j]
               for i in range(2) for j in range(2))
