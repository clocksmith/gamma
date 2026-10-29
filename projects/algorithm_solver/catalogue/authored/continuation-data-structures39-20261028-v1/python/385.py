"""Original frontend 385 variant; qualification unknown."""


class NestedInteger:
    def __init__(self, value=None):
        if value is None:
            self._is_int = False
            self._val = None
            self._list = []
        else:
            self._is_int = True
            self._val = int(value)
            self._list = []

    def isInteger(self) -> bool:
        return self._is_int

    def add(self, elem) -> None:
        self._list.append(elem)

    def setInteger(self, value: int) -> None:
        self._is_int = True
        self._val = int(value)

    def getInteger(self):
        return self._val if self._is_int else None

    def getList(self):
        return None if self._is_int else self._list

    def to_python(self):
        if self._is_int:
            return self._val
        return [x.to_python() for x in self._list]


def _parse_nested(s: str) -> NestedInteger:
    if s[0] != "[":
        return NestedInteger(int(s))
    stack = []
    num = 0
    sign = 1
    in_num = False
    for ch in s:
        if ch == "[":
            stack.append(NestedInteger())
        elif ch == "-":
            sign = -1
        elif "0" <= ch <= "9":
            num = num * 10 + (ord(ch) - 48)
            in_num = True
        elif ch in (",", "]"):
            if in_num:
                stack[-1].add(NestedInteger(sign * num))
                num = 0
                sign = 1
                in_num = False
            if ch == "]" and len(stack) > 1:
                top = stack.pop()
                stack[-1].add(top)
    return stack[0]


def solve(s: str):
    return _parse_nested(s).to_python()


deserialize = solve


class Solution:
    def deserialize(self, s: str):
        return solve(s)
