"""1871. Jump Game VII: maintain the count of reachable predecessors in the permitted jump window."""


def solve(s: str, minJump: int, maxJump: int) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    reachable = bytearray(len(s))
    reachable[0] = 1
    active = 0
    for index in range(1, len(s)):
        if index >= minJump:
            active += reachable[index - minJump]
        if index > maxJump:
            active -= reachable[index - maxJump - 1]
        if s[index] == '0' and active > 0:
            reachable[index] = 1
    return bool(reachable[-1])


class Solution:
    def canReach(self, s: str, minJump: int, maxJump: int) -> bool:
        return solve(s, minJump, maxJump)
