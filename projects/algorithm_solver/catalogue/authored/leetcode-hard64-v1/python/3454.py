"""3454. Separate Squares II: sweep union-covered horizontal strips with a segment tree."""


def solve(squares: list[list[int]]) -> float:
    """O(n log n) time and O(n) auxiliary space. Inputs are preserved."""
    coordinates = sorted({coordinate for x, _, side in squares for coordinate in (x, x + side)})
    index_of = {coordinate: index for index, coordinate in enumerate(coordinates)}
    segments = len(coordinates) - 1
    cover = [0] * (4 * segments)
    length = [0] * (4 * segments)
    events = []
    for x, y, side in squares:
        first, last = index_of[x], index_of[x + side] - 1
        events.append((y, 1, first, last))
        events.append((y + side, -1, first, last))
    events.sort()

    def update(node, left, right, first, last, change):
        if first <= left and right <= last:
            cover[node] += change
        else:
            middle = (left + right) // 2
            if first <= middle:
                update(2 * node, left, middle, first, last, change)
            if last > middle:
                update(2 * node + 1, middle + 1, right, first, last, change)
        if cover[node]:
            length[node] = coordinates[right + 1] - coordinates[left]
        elif left == right:
            length[node] = 0
        else:
            length[node] = length[2 * node] + length[2 * node + 1]

    strips = []
    total = 0
    previous_y = events[0][0]
    position = 0
    while position < len(events):
        y = events[position][0]
        if y > previous_y:
            width = length[1]
            strips.append((previous_y, y, width))
            total += (y - previous_y) * width
        while position < len(events) and events[position][0] == y:
            _, change, first, last = events[position]
            update(1, 0, segments - 1, first, last, change)
            position += 1
        previous_y = y
    accumulated = 0
    for bottom, top, width in strips:
        area = (top - bottom) * width
        if width and 2 * (accumulated + area) >= total:
            return bottom + (total - 2 * accumulated) / (2 * width)
        accumulated += area
    return float(previous_y)


class Solution:
    def separateSquares(self, squares: list[list[int]]) -> float:
        return solve(squares)
