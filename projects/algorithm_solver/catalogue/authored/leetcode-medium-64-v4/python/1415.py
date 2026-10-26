"""1415. The k-th Lexicographical String of All Happy Strings of Length n: skip lexicographic blocks using their exact binary suffix counts."""


def solve(n: int, k: int) -> str:
    """O(n) time and O(n) space including the result on the declared n <= 10 domain; inputs are read-only."""
    if k > 3 * (1 << (n - 1)):
        return ''
    result = []
    rank = k
    for index in range(n):
        block = 1 << (n - index - 1)
        for letter in 'abc':
            if result and result[-1] == letter:
                continue
            if rank > block:
                rank -= block
            else:
                result.append(letter)
                break
    return ''.join(result)


class Solution:
    def getHappyString(self, n: int, k: int) -> str:
        return solve(n, k)
