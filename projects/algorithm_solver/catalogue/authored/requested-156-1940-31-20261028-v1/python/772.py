"""Original frontend 772 variant; qualification unknown."""


def solve(s: str) -> int:
    idx = 0
    n = len(s)

    def parse_expr():
        nonlocal idx
        stack = []
        num = 0
        op = "+"
        while idx < n:
            ch = s[idx]
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == "(":
                idx += 1
                num = parse_expr()
            if (not ch.isdigit() and ch != " ") or idx == n - 1:
                if op == "+":
                    stack.append(num)
                elif op == "-":
                    stack.append(-num)
                elif op == "*":
                    stack.append(stack.pop() * num)
                elif op == "/":
                    stack.append(int(stack.pop() / num))
                op = ch
                num = 0
                if ch == ")":
                    break
            idx += 1
        return sum(stack)

    return parse_expr()


calculate = solve


class Solution:
    def calculate(self, s: str) -> int:
        return solve(s)
