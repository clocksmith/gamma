"""246. Strobogrammatic Number."""
def solve(num: str) -> bool:
    mapping = {'0': '0', '1': '1', '6': '9', '8': '8', '9': '6'}
    return all(char in mapping and mapping[char] == num[-index - 1] for index, char in enumerate(num))

class Solution:
    def isStrobogrammatic(self, num: str) -> bool:
        return solve(num)
