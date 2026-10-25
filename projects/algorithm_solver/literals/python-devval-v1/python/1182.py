from bisect import bisect_left


def solve(colors, queries):
    positions = [[], [], []]
    for index, color in enumerate(colors):
        positions[color - 1].append(index)
    result = []
    for index, color in queries:
        choices = positions[color - 1]
        if not choices:
            result.append(-1)
            continue
        right = bisect_left(choices, index)
        distance = len(colors) + 1
        if right < len(choices):
            distance = choices[right] - index
        if right:
            distance = min(distance, index - choices[right - 1])
        result.append(distance)
    return result
