'use strict';

// 207. Course Schedule (Medium).
// Specification: https://leetcode.com/problems/course-schedule/description/
function solve(numCourses, prerequisites) {
  const graph = Array.from({ length: numCourses }, () => []);
  const indegree = new Array(numCourses).fill(0);
  for (const [course, prerequisite] of prerequisites) { graph[prerequisite].push(course); indegree[course]++; }
  const queue = [];
  for (let i = 0; i < numCourses; i++) { if (indegree[i] === 0) queue.push(i); }
  let finished = 0;
  while (queue.length > 0) {
    const course = queue.shift();
    finished++;
    for (const next of graph[course]) { indegree[next]--; if (indegree[next] === 0) queue.push(next); }
  }
  return finished === numCourses;
}
const canFinish = solve;
class Solution { canFinish(numCourses, prerequisites) { return solve(numCourses, prerequisites); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canFinish };
