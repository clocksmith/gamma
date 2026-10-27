"""394. Decode String. Decode nested groups with an explicit stack."""

def solve(s: str) -> str:
    stack = []
    parts = []
    repeat = 0
    for char in s:
        if '0' <= char <= '9':
            repeat = repeat * 10 + ord(char) - 48
        elif char == '[':
            stack.append((parts, repeat))
            parts, repeat = [], 0
        elif char == ']':
            previous, count = stack.pop()
            previous.append(''.join(parts) * count)
            parts = previous
        else:
            parts.append(char)
    return ''.join(parts)


class Solution:
    def decodeString(self, s: str) -> str:
        return solve(s)
