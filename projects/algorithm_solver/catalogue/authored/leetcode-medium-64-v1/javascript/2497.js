'use strict';

// 2497. Maximum Star Sum of a Graph: add at most k positive neighbor values to each possible center.
// O(n + e * log(e + 1)) time and O(n + e) auxiliary space; inputs are read-only.
function solve(vals, edges, k) {
  let answer = -Infinity;
  for (const value of vals) answer = Math.max(answer, value);
  if (k === 0) return answer;
  const neighbors = Array.from({ length: vals.length }, () => []);
  for (const [left, right] of edges) {
    if (vals[right] > 0) neighbors[left].push(vals[right]);
    if (vals[left] > 0) neighbors[right].push(vals[left]);
  }
  for (let node = 0; node < vals.length; node += 1) {
    const values = neighbors[node];
    values.sort((left, right) => right - left);
    let total = vals[node];
    for (let index = 0; index < Math.min(k, values.length); index += 1) total += values[index];
    answer = Math.max(answer, total);
  }
  return answer;
}

const maxStarSum = solve;
class Solution {
  maxStarSum(vals, edges, k) { return solve(vals, edges, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxStarSum };
