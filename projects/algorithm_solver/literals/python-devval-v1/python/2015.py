def solve(buildings):
    events = {}
    for start, end, height in buildings:
        start_event = events.setdefault(start, [0, 0])
        start_event[0] += height
        start_event[1] += 1
        end_event = events.setdefault(end, [0, 0])
        end_event[0] -= height
        end_event[1] -= 1
    coordinates = sorted(events)
    total_height = 0
    active = 0
    result = []
    for index in range(len(coordinates) - 1):
        start = coordinates[index]
        end = coordinates[index + 1]
        total_height += events[start][0]
        active += events[start][1]
        if active:
            average = total_height // active
            if result and result[-1][1] == start and result[-1][2] == average:
                result[-1][1] = end
            else:
                result.append([start, end, average])
    return result
