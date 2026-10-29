"""Original frontend 753 variant; qualification unknown."""

def solve(n, k):
    modulus = k ** (n - 1)
    used = [0] * modulus
    stack = [(0, -1)]
    digits = []
    while stack:
        node, digit = stack[-1]
        if used[node] < k:
            edge = used[node]
            used[node] += 1
            stack.append(((node * k + edge) % modulus, edge))
        else:
            stack.pop()
            if digit >= 0:
                digits.append(str(digit))
    digits.reverse()
    return '0' * (n - 1) + ''.join(digits)


class Solution:
    def crackSafe(self, n, k):
        return solve(n, k)
