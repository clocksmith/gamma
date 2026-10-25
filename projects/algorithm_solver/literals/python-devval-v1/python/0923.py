def solve(values, target):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    ordered = sorted(counts)
    result = 0
    for first_index, first in enumerate(ordered):
        for second in ordered[first_index:]:
            third = target - first - second
            if third < second or third not in counts:
                continue
            a, b, c = counts[first], counts[second], counts[third]
            if first == third:
                combinations = a * (a - 1) * (a - 2) // 6
            elif first == second:
                combinations = a * (a - 1) // 2 * c
            elif second == third:
                combinations = a * b * (b - 1) // 2
            else:
                combinations = a * b * c
            result = (result + combinations) % 1000000007
    return result
