def solve(connected):
    count = len(connected)
    visited = [False] * count
    provinces = 0
    for start in range(count):
        if visited[start]:
            continue
        provinces += 1
        visited[start] = True
        pending = [start]
        while pending:
            city = pending.pop()
            for neighbor in range(count):
                if connected[city][neighbor] and not visited[neighbor]:
                    visited[neighbor] = True
                    pending.append(neighbor)
    return provinces
