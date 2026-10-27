'use strict';

// 596. Classes With at Least 5 Students. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. courses: student, class. Output: class. Counts distinct students per class.

function solve(courses) {
  const groups = new Map();
  for (const row of courses) {
    if (!groups.has(row.class)) groups.set(row.class, new Set());
    groups.get(row.class).add(row.student);
  }
  return [...groups.keys()].sort().filter(name => groups.get(name).size >= 5).map(name => ({class: name}));
}

const findClasses = solve;
class Solution {
  findClasses(courses) { return solve(courses); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findClasses };
