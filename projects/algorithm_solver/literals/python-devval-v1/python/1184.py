def solve(distances, start, destination):
    total = sum(distances)
    clockwise = 0
    while start != destination:
        clockwise += distances[start]
        start = (start + 1) % len(distances)
    return min(clockwise, total - clockwise)
