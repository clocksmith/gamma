def solve(times):
    if len(times) > 1440:
        return 0
    minutes = sorted(int(value[:2]) * 60 + int(value[3:]) for value in times)
    best = minutes[0] + 1440 - minutes[-1]
    for index in range(1, len(minutes)):
        best = min(best, minutes[index] - minutes[index - 1])
    return best
