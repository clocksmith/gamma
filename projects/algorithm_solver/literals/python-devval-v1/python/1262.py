def solve(values):
    best = [0, None, None]
    for value in values:
        updated = best[:]
        for total in best:
            if total is not None:
                candidate = total + value
                remainder = candidate % 3
                if updated[remainder] is None or candidate > updated[remainder]:
                    updated[remainder] = candidate
        best = updated
    return best[0]
