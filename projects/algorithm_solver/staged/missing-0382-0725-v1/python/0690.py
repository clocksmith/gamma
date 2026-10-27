"""690. Employee Importance. Read Employee objects (or equivalent records) and count each reachable employee once."""

def solve(employees, id):
    def field(employee, name):
        return employee[name] if isinstance(employee, dict) else getattr(employee, name)
    by_id = {field(employee, 'id'): employee for employee in employees}
    stack, seen = [id], set()
    answer = 0
    while stack:
        identifier = stack.pop()
        if identifier in seen:
            continue
        seen.add(identifier)
        employee = by_id[identifier]
        answer += field(employee, 'importance')
        stack.extend(field(employee, 'subordinates'))
    return answer


class Solution:
    def getImportance(self, employees, id):
        return solve(employees, id)
