def solve(users, timestamps, websites):
    visits = {}
    for index in sorted(range(len(users)), key=lambda index: timestamps[index]):
        visits.setdefault(users[index], []).append(websites[index])
    counts = {}
    for history in visits.values():
        patterns = set()
        for first in range(len(history) - 2):
            for second in range(first + 1, len(history) - 1):
                for third in range(second + 1, len(history)):
                    patterns.add((history[first], history[second], history[third]))
        for pattern in patterns:
            counts[pattern] = counts.get(pattern, 0) + 1
    best = min(counts, key=lambda pattern: (-counts[pattern], pattern))
    return list(best)
