'use strict';

// 210. Course Schedule II (Medium).
// Specification: https://leetcode.com/problems/course-schedule-ii/description/
function solve(numCourses, prerequisites) {
  const graph = Array.from({ length: numCourses }, () => []);
  const indegree = new Array(numCourses).fill(0);
  for (const [course, prerequisite] of prerequisites) { graph[prerequisite].push(course); indegree[course]++; }
  const queue = [];
  for (let i = 0; i < numCourses; i++) { if (indegree[i] === 0) queue.push(i); }
  const result = [];
  while (queue.length > 0) {
    const course = queue.shift();
    result.push(course);
    for (const next of graph[course]) { indegree[next]--; if (indegree[next] === 0) queue.push(next); }
  }
  return result.length === numCourses ? result : [];
}
const findOrder = solve;
class Solution { findOrder(numCourses, prerequisites) { return solve(numCourses, prerequisites); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findOrder };
