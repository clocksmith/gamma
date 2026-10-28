def solve(s, t):
    remaining = [t.count('0'), t.count('1')]
    output = []
    for c in s:
        bit = int(c)
        desired = 1 - bit
        chosen = desired if remaining[desired] else bit
        remaining[chosen] -= 1
        output.append(str(bit ^ chosen))
    return ''.join(output)


class Solution:
    def maximumXor(self, s, t):
        return solve(s, t)
