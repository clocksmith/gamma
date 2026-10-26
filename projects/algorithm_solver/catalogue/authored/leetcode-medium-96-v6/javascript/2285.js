'use strict';

// 2285. Maximum Total Importance of Roads: assign the largest labels to vertices with the largest degrees.
// O(n log n + e) time and O(n) auxiliary space; inputs are read-only.
function solve(n, roads) {
  const degree = new Array(n).fill(0);
  for (const [left, right] of roads) {
    degree[left] += 1;
    degree[right] += 1;
  }
  degree.sort((left, right) => left - right);
  let total = 0;
  for (let index = 0; index < n; index += 1) total += (index + 1) * degree[index];
  return total;
}

const maximumImportance = solve;
class Solution {
  maximumImportance(n, roads) { return solve(n, roads); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumImportance };
