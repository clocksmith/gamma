def solve(values):
    lengths = [1] * len(values)
    counts = [1] * len(values)
    longest = 0
    answer = 0
    for end, value in enumerate(values):
        for previous in range(end):
            if values[previous] < value:
                candidate = lengths[previous] + 1
                if candidate > lengths[end]:
                    lengths[end] = candidate
                    counts[end] = counts[previous]
                elif candidate == lengths[end]:
                    counts[end] += counts[previous]
        if lengths[end] > longest:
            longest = lengths[end]
            answer = counts[end]
        elif lengths[end] == longest:
            answer += counts[end]
    return answer
