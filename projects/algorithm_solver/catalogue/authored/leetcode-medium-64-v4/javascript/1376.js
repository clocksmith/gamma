'use strict';

// 1376. Time Needed to Inform All Employees: propagate message arrival times through an iterative hierarchy traversal.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, headID, manager, informTime) {
  const children = Array.from({ length: n }, () => []);
  for (let employee = 0; employee < n; employee += 1) {
    if (manager[employee] !== -1) children[manager[employee]].push(employee);
  }
  const stack = [[headID, 0]];
  let latest = 0;
  while (stack.length) {
    const [employee, arrival] = stack.pop();
    latest = Math.max(latest, arrival);
    const following = arrival + informTime[employee];
    for (const child of children[employee]) stack.push([child, following]);
  }
  return latest;
}

const numOfMinutes = solve;
class Solution {
  numOfMinutes(n, headID, manager, informTime) { return solve(n, headID, manager, informTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfMinutes };
