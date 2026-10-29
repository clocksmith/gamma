"""Hack2Hire 68811dddf96758aa78e1d688 (Calculate Equation Expression, level 2) over an INFERRED spec; qualification unknown."""


def parse(arr):
    defs = {}
    for line in arr[1:]:
        tokens = line.split(' ')
        terms = [('+', tokens[2])] + [(tokens[i], tokens[i + 1]) for i in range(3, len(tokens), 2)]
        defs[tokens[0]] = [(sign, int(tok) if tok[0].isdigit() else tok) for sign, tok in terms]
    return defs


def evaluate(target, defs):
    """Iterative three-colour post-order DFS: 1 = on the current path, 2 = evaluated, 3 = failed."""
    state, value = {}, {}
    stack = [target]
    while stack:
        name = stack[-1]
        st = state.get(name, 0)
        if st == 0:
            if name not in defs:
                state[name] = 3
                stack.pop()
                continue
            state[name] = 1
            for _, op in defs[name]:
                if type(op) is str and state.get(op, 0) == 0:
                    stack.append(op)
        elif st == 1:
            stack.pop()
            total = 0
            for sign, op in defs[name]:
                if type(op) is int:
                    v = op
                elif state.get(op, 0) == 2:
                    v = value[op]
                else:
                    state[name] = 3
                    break
                total = total + v if sign == '+' else total - v
            else:
                state[name] = 2
                value[name] = total
        else:
            stack.pop()
    return value.get(target)


def solve(arr):
    return evaluate(arr[0], parse(arr))


class Solution:
    def calculate(self, arr):
        return solve(arr)
