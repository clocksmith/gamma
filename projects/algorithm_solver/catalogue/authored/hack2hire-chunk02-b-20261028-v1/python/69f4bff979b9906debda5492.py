"""Original Hack2Hire 69f4bff979b9906debda5492 variant over an INFERRED specification (request helper modelled as an injected map); qualification unknown."""
from collections import deque

NOT_FOUND = {'message': 'Not Found', 'next': []}
UNAUTHORIZED = {'message': 'Unauthorized', 'next': []}


def solve(maze):
    def request(url, headers):
        entry = maze.get(url, NOT_FOUND)
        for key, value in entry.get('requiredHeaders', {}).items():
            if headers.get(key) != value:
                return UNAUTHORIZED
        return entry
    queue, seen = deque([('/', {})]), {'/'}
    while queue:
        url, headers = queue.popleft()
        response = request(url, headers)
        if response['message'] == 'Congrats':
            return url
        forward = response.get('headers', {})
        for nxt in response['next']:
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, forward))
    return ''


class Solution:
    def findMazeExitWithHeaders(self, maze):
        return solve(maze)
