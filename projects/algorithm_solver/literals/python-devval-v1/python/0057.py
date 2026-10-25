def solve(intervals, new_interval):
    low, high = new_interval
    result = []
    index = 0
    while index < len(intervals) and intervals[index][1] < low:
        result.append(intervals[index])
        index += 1
    while index < len(intervals) and intervals[index][0] <= high:
        low = min(low, intervals[index][0])
        high = max(high, intervals[index][1])
        index += 1
    result.append([low, high])
    result.extend(intervals[index:])
    return result
