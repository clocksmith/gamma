'use strict';

// 1462. Course Schedule IV: compute transitive reachability once before answering prerequisite queries.
// O(v^3 + q) time and O(v^2) auxiliary space; inputs are read-only.
function solve(numCourses, prerequisites, queries) {
  const reachable = Array.from({ length: numCourses }, () => new Uint8Array(numCourses));
  for (const [first, second] of prerequisites) reachable[first][second] = 1;
  for (let middle = 0; middle < numCourses; middle += 1) {
    for (let first = 0; first < numCourses; first += 1) {
      if (!reachable[first][middle]) continue;
      for (let second = 0; second < numCourses; second += 1) {
        if (reachable[middle][second]) reachable[first][second] = 1;
      }
    }
  }
  return queries.map(([first, second]) => Boolean(reachable[first][second]));
}

const checkIfPrerequisite = solve;
class Solution {
  checkIfPrerequisite(numCourses, prerequisites, queries) { return solve(numCourses, prerequisites, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkIfPrerequisite };
