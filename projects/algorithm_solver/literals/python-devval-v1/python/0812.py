def solve(points):
    best_double_area = 0
    for first in range(len(points)):
        x0, y0 = points[first]
        for second in range(first + 1, len(points)):
            dx1 = points[second][0] - x0
            dy1 = points[second][1] - y0
            for third in range(second + 1, len(points)):
                dx2 = points[third][0] - x0
                dy2 = points[third][1] - y0
                best_double_area = max(best_double_area, abs(dx1 * dy2 - dx2 * dy1))
    return best_double_area / 2
