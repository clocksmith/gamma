"""580. Count Student Number in Departments. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. student: student_id, student_name, gender, dept_id; department: dept_id, dept_name. Output: dept_name, student_number, including empty departments."""

def solve(student, department):
    counts = {}
    for row in student:
        counts[row['dept_id']] = counts.get(row['dept_id'], 0) + 1
    result = [{'dept_name': row['dept_name'], 'student_number': counts.get(row['dept_id'], 0)} for row in department]
    return sorted(result, key=lambda row: (-row['student_number'], row['dept_name']))


class Solution:
    def countStudents(self, student, department):
        return solve(student, department)
