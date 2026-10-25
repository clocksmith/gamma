def solve(values, target):
    infinity = len(values) + 1
    best_prefix = [infinity] * len(values)
    best_pair = infinity
    total = 0
    left = 0
    for right, value in enumerate(values):
        total += value
        while total > target:
            total -= values[left]
            left += 1
        shortest = best_prefix[right - 1] if right else infinity
        if total == target:
            length = right - left + 1
            if left:
                best_pair = min(best_pair, best_prefix[left - 1] + length)
            shortest = min(shortest, length)
        best_prefix[right] = shortest
    return -1 if best_pair == infinity else best_pair
