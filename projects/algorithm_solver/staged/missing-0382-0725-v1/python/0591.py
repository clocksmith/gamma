"""591. Tag Validator. Parse one enclosing root, matched uppercase tags, and opaque CDATA sections."""

def solve(code: str) -> bool:
    if not code or code[0] != '<':
        return False
    stack = []
    i = 0
    while i < len(code):
        if i and not stack:
            return False
        if code.startswith('<![CDATA[', i):
            if not stack:
                return False
            end = code.find(']]>', i + 9)
            if end == -1:
                return False
            i = end + 3
        elif code.startswith('</', i):
            end = code.find('>', i + 2)
            if end == -1 or not stack or stack.pop() != code[i + 2:end]:
                return False
            i = end + 1
        elif code[i] == '<':
            end = code.find('>', i + 1)
            if end == -1:
                return False
            name = code[i + 1:end]
            if not 1 <= len(name) <= 9 or any(not 'A' <= char <= 'Z' for char in name):
                return False
            stack.append(name)
            i = end + 1
        else:
            i += 1
    return not stack


class Solution:
    def isValid(self, code: str) -> bool:
        return solve(code)
