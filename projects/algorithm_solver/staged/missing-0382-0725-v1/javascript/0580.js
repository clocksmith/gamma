'use strict';

// 580. Count Student Number in Departments. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. student: student_id, student_name, gender, dept_id; department: dept_id, dept_name. Output: dept_name, student_number, including empty departments.

function solve(student, department) {
  const counts = new Map();
  for (const row of student) counts.set(row.dept_id, (counts.get(row.dept_id) || 0) + 1);
  return department.map(row => ({dept_name: row.dept_name, student_number: counts.get(row.dept_id) || 0}))
    .sort((a, b) => b.student_number - a.student_number || (a.dept_name < b.dept_name ? -1 : a.dept_name > b.dept_name ? 1 : 0));
}

const countStudents = solve;
class Solution {
  countStudents(student, department) { return solve(student, department); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countStudents };
