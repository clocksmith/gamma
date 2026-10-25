def solve(rooms):
    visited = {0}
    pending = [0]
    while pending:
        room = pending.pop()
        for key in rooms[room]:
            if key not in visited:
                visited.add(key)
                pending.append(key)
    return len(visited) == len(rooms)
