def solve(workers, bikes):
    by_distance = {}
    for worker, (wx, wy) in enumerate(workers):
        for bike, (bx, by) in enumerate(bikes):
            distance = abs(wx - bx) + abs(wy - by)
            by_distance.setdefault(distance, []).append((worker, bike))
    used_workers = set()
    used_bikes = set()
    assignments = [0] * len(workers)
    for distance in sorted(by_distance):
        for worker, bike in by_distance[distance]:
            if worker not in used_workers and bike not in used_bikes:
                assignments[worker] = bike
                used_workers.add(worker)
                used_bikes.add(bike)
    return assignments
