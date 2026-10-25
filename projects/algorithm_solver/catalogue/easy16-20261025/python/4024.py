def solve(drones: list[list[int]], target: list[int]) -> int:
    """Keep the first reachable minimum-distance drone. O(n) time, O(1) space."""
    answer = -1
    best_distance = float("inf")
    for index, (x, y, travel_range) in enumerate(drones):
        distance = abs(x - target[0]) + abs(y - target[1])
        if distance <= travel_range and distance < best_distance:
            answer = index
            best_distance = distance
    return answer
