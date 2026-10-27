"""596. Classes With at Least 5 Students. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. courses: student, class. Output: class. Counts distinct students per class."""

def solve(courses):
    groups = {}
    for row in courses:
        groups.setdefault(row['class'], set()).add(row['student'])
    return [{'class': name} for name in sorted(groups) if len(groups[name]) >= 5]


class Solution:
    def findClasses(self, courses):
        return solve(courses)
