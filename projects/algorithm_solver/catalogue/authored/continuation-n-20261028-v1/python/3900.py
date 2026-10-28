"""Original frontend 3900 variant; qualification unknown."""

def solve(s):
    cap = 2 * min(s.count('0'), s.count('1'))
    if cap == 0:
        return 0
    positions = {0: [0]}
    heads = {0: 0}
    difference = answer = 0
    for right, char in enumerate(s, 1):
        difference += 1 if char == '1' else -1
        positions.setdefault(difference, []).append(right)
        heads.setdefault(difference, 0)
        for key in (difference - 2, difference, difference + 2):
            if key not in positions:
                continue
            indices = positions[key]
            head = heads[key]
            while head < len(indices) and indices[head] < right - cap:
                head += 1
            heads[key] = head
            if head < len(indices):
                answer = max(answer, right - indices[head])
    return answer


class Solution:
    def longestBalanced(self, s):
        return solve(s)
