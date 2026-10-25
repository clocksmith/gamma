def solve(counts):
    total = sum(counts)
    minimum = next(index for index, count in enumerate(counts) if count)
    maximum = next(index for index in range(len(counts) - 1, -1, -1) if counts[index])
    weighted = sum(index * count for index, count in enumerate(counts))
    mode = max(range(len(counts)), key=lambda index: counts[index])
    first_rank = (total + 1) // 2
    second_rank = total // 2 + 1
    cumulative = 0
    first_middle = None
    second_middle = None
    for value, count in enumerate(counts):
        cumulative += count
        if first_middle is None and cumulative >= first_rank:
            first_middle = value
        if cumulative >= second_rank:
            second_middle = value
            break
    return [minimum, maximum, weighted / total, (first_middle + second_middle) / 2, mode]
