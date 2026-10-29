"""Original Hack2Hire 69f3d14942791c82ab992e68 variant over an INFERRED specification (request helper modelled as an injected map); qualification unknown."""
from collections import deque

NOT_FOUND = {'message': 'Not Found', 'next': []}


def solve(maze):
    def request(url, headers):
        return maze.get(url, NOT_FOUND)
    queue, seen = deque(['/']), {'/'}
    while queue:
        url = queue.popleft()
        response = request(url, {})
        if response['message'] == 'Congrats':
            return url
        for nxt in response['next']:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return ''


class Solution:
    def findMazeExit(self, maze):
        return solve(maze)
