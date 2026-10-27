"""636. Exclusive Time of Functions."""

def solve(n: int, logs: list[str]) -> list[int]:
    answer = [0] * n
    stack = []
    previous = 0
    for log in logs:
        identifier, event, timestamp = log.split(':')
        identifier, timestamp = int(identifier), int(timestamp)
        if event == 'start':
            if stack:
                answer[stack[-1]] += timestamp - previous
            stack.append(identifier)
            previous = timestamp
        else:
            answer[stack.pop()] += timestamp - previous + 1
            previous = timestamp + 1
    return answer


class Solution:
    def exclusiveTime(self, n: int, logs: list[str]) -> list[int]:
        return solve(n, logs)
