"""394. Decode String (Medium).

Specification: https://leetcode.com/problems/decode-string/description/
"""


def solve(s: str) -> str:
    count_stack = []
    string_stack = []
    current = ''
    number = 0
    for ch in s:
        if ch.isdigit():
            number = number * 10 + int(ch)
        elif ch == '[':
            count_stack.append(number)
            string_stack.append(current)
            current = ''
            number = 0
        elif ch == ']':
            repeat = count_stack.pop()
            previous = string_stack.pop()
            current = previous + current * repeat
        else:
            current += ch
    return current


class Solution:
    def decodeString(self, s: str) -> str:
        return solve(s)
