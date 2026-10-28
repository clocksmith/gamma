"""1271. Hexspeak (Easy).

Specification: https://leetcode.com/problems/hexspeak/description/
"""


def solve(num: int) -> str:
    hex_text = format(num, 'X')
    result = ''
    for ch in hex_text:
        if ch == '0':
            result += 'O'
        elif ch == '1':
            result += 'I'
        elif 'A' <= ch <= 'F':
            result += ch
        else:
            return 'ERROR'
    return result


class Solution:
    def toHexspeak(self, num: int) -> str:
        return solve(num)
