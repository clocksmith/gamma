def solve(n, l, r):
    modulus = 1000000007
    width = r-l+1
    up, down = [1]*width, [1]*width
    for _ in range(1,n):
        next_up, next_down = [0]*width, [0]*width
        prefix = suffix = 0
        for i in range(width):
            next_up[i] = prefix
            prefix = (prefix+down[i]) % modulus
            j = width-1-i
            next_down[j] = suffix
            suffix = (suffix+up[j]) % modulus
        up, down = next_up, next_down
    return (sum(up)+sum(down)) % modulus

class Solution:
    def zigZagArrays(self, n, l, r):
        return solve(n, l, r)
