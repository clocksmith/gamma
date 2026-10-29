"""Original LeetCode 690 candidate; qualification unknown."""

def solve(employees, id):
    lookup = {employee.id: employee for employee in employees}
    total, stack, seen = 0, [id], set()
    while stack:
        key = stack.pop()
        if key in seen: continue
        seen.add(key)
        employee = lookup[key]
        total += employee.importance
        stack.extend(employee.subordinates)
    return total


class Solution:
    def getImportance(self, employees, id):
        return solve(employees, id)
