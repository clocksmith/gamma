"""247. Strobogrammatic Number II."""
def solve(n: int) -> list[str]:
    pairs = [('0', '0'), ('1', '1'), ('6', '9'), ('8', '8'), ('9', '6')]
    def build(length: int, outer: int):
        if length == 0:
            return ['']
        if length == 1:
            return ['0', '1', '8']
        result = []
        for middle in build(length - 2, outer):
            for left, right in pairs:
                if length == outer and left == '0':
                    continue
                result.append(left + middle + right)
        return result
    return build(n, n)

class Solution:
    def findStrobogrammatic(self, n: int) -> list[str]:
        return solve(n)
