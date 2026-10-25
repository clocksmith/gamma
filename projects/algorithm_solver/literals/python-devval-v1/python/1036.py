def solve(blocked, source, target):
    forbidden = {tuple(cell) for cell in blocked}
    limit = len(blocked) * (len(blocked) - 1) // 2

    def escapes(start, destination):
        start = tuple(start)
        destination = tuple(destination)
        seen = {start}
        queue = [start]
        head = 0
        while head < len(queue):
            row, column = queue[head]
            head += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, column + dc)
                if not (0 <= neighbor[0] < 1000000 and 0 <= neighbor[1] < 1000000):
                    continue
                if neighbor in seen or neighbor in forbidden:
                    continue
                if neighbor == destination:
                    return True
                seen.add(neighbor)
                if len(seen) > limit:
                    return True
                queue.append(neighbor)
        return False

    return escapes(source, target) and escapes(target, source)
