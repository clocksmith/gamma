class Solution:
    def parseBoolExpr(self, expression: str) -> bool:
        stack = []
        for token in expression:
            if token == ",":
                continue
            if token != ")":
                stack.append(token)
                continue
            seen_true = False
            seen_false = False
            while stack[-1] != "(":
                value = stack.pop()
                if value == "t":
                    seen_true = True
                else:
                    seen_false = True
            stack.pop()
            operator = stack.pop()
            if operator == "!":
                result = not seen_true
            elif operator == "&":
                result = not seen_false
            else:
                result = seen_true
            stack.append("t" if result else "f")
        return stack[0] == "t"
