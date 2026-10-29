"""Original development candidate; qualification unknown."""
def solve(s, k):
    length = 0
    for ch in s:
        length = length*int(ch) if ch.isdigit() else length+1
    for ch in reversed(s):
        k %= length
        if ch.isalpha():
            if k == 0:
                return ch
            length -= 1
        else:
            length //= int(ch)


class Solution:
    def decodeAtIndex(self, s, k):
        return solve(s, k)
