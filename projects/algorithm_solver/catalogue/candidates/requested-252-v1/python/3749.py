"""3749. Evaluate Valid Expressions
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(expression).
Algorithm: Iterative operator/value stacks; no recursive descent and no eval.
Complexity: O(expression length) arithmetic operations and space; integer operands bounded by the stated long range.
Numeric semantics: JavaScript solve and evaluateExpression return BigInt; Python returns int. Both solveJson functions return an exact decimal string. Never coerce a signed 64-bit result to an unsafe Number.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: solve(expression) and evaluateExpression; explicit solveJson adapter for JSON transport. Gamma exact-integer adapter remains pending.
Specification: https://leetcode.com/problems/evaluate-valid-expressions/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3749.Evaluate%20Valid%20Expressions/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(expression):
    operators = []
    values = []
    index = 0
    while index < len(expression):
        character = expression[index]
        if character == "-" or "0" <= character <= "9":
            end = index + (character == "-")
            while end < len(expression) and "0" <= expression[end] <= "9":
                end += 1
            values.append(int(expression[index:end]))
            index = end
        elif "a" <= character <= "z":
            operator = expression[index:index + 3]
            if operator not in ("add", "sub", "mul", "div"):
                raise ValueError("Unknown operator.")
            operators.append(operator)
            index += 3
        elif character == ")":
            right = values.pop()
            left = values.pop()
            operator = operators.pop()
            if operator == "add":
                value = left + right
            elif operator == "sub":
                value = left - right
            elif operator == "mul":
                value = left * right
            else:
                if right == 0 or left % right:
                    raise ValueError("Division must have a nonzero divisor and exact integer result.")
                value = left // right
            values.append(value)
            index += 1
        elif character in "(,":
            index += 1
        else:
            raise ValueError("Unexpected expression character.")
    if operators or len(values) != 1:
        raise ValueError("Incomplete expression.")
    return values[0]


def solveJson(expression):
    return str(solve(expression))


def evaluateExpression(expression):
    return solve(expression)


class Solution:
    def evaluateExpression(self, expression):
        return solve(expression)
