"""Original frontend 726 variant; qualification unknown."""

def solve(formula):
    counts = {}
    multipliers = [1]
    pending = 1
    i = len(formula) - 1
    while i >= 0:
        char = formula[i]
        if char.isdigit():
            j = i
            while formula[j - 1].isdigit():
                j -= 1
            pending = int(formula[j:i + 1])
            i = j - 1
        elif char == ')':
            multipliers.append(multipliers[-1] * pending)
            pending = 1
            i -= 1
        elif char == '(':
            multipliers.pop()
            i -= 1
        else:
            j = i
            while formula[j].islower():
                j -= 1
            name = formula[j:i + 1]
            counts[name] = counts.get(name, 0) + pending * multipliers[-1]
            pending = 1
            i = j - 1
    return ''.join(name + (str(counts[name]) if counts[name] > 1 else '') for name in sorted(counts))


class Solution:
    def countOfAtoms(self, formula):
        return solve(formula)
