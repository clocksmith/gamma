"""Hack2Hire 691e0f0208ad7861624b5677 (Print Employee Org Chart) over an INFERRED spec; qualification unknown."""


def solve(employees):
    reports = {}
    names = {}
    ceo = None
    for emp_id, manager_id, name in employees:
        names[emp_id] = name
        if emp_id == manager_id:
            ceo = emp_id
        else:
            reports.setdefault(manager_id, []).append(emp_id)
    lines = []
    stack = [(ceo, 0)]
    while stack:
        emp_id, depth = stack.pop()
        lines.append('-' * (4 * depth) + names[emp_id])
        kids = reports.get(emp_id)
        if kids:
            for kid in reversed(kids):  # first report printed first
                stack.append((kid, depth + 1))
    return '\n'.join(lines)


class Solution:
    def printOrgChart(self, employees):
        return solve(employees)
