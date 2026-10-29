"""Hack2Hire 68c4834e97640ed3834dc7ca (Hopscotch) over an INFERRED spec; qualification unknown."""


def solve(s, start):
    n = len(s)
    if s[start] == 'X':
        return -1
    dist = [-1] * n
    dist[start] = 0
    queue = [start]
    head = 0
    while head < len(queue):
        i = queue[head]
        head += 1
        if i == n - 1:
            return dist[i]
        cell = s[i]
        j = 0
        while j < len(cell):
            direction = cell[j]
            j += 1
            step = 0
            while j < len(cell) and '0' <= cell[j] <= '9':
                step = step * 10 + ord(cell[j]) - 48
                j += 1
            if step == 0:
                step = 1
            target = i + step if direction == 'R' else i - step
            if 0 <= target < n and dist[target] < 0 and s[target] != 'X':
                dist[target] = dist[i] + 1
                queue.append(target)
    return -1


class Solution:
    def minJumps(self, s, start):
        return solve(s, start)
