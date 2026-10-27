# Original candidate implementation. Contract: https://leetcode.com/problems/describe-the-painting/
def solve(segments):
    events = {}
    for left, right, color in segments:
        events[left] = events.get(left, 0) + color
        events[right] = events.get(right, 0) - color
    answer, previous, total = [], None, 0
    for point in sorted(events):
        if previous is not None and total:
            answer.append([previous, point, total])
        total += events[point]
        previous = point
    return answer
