'use strict';

// 973. K Closest Points to Origin (Medium).
// Specification: https://leetcode.com/problems/k-closest-points-to-origin/description/
function solve(points, k) {
  const sorted = points.slice().sort((a, b) => {
    const da = a[0] * a[0] + a[1] * a[1];
    const db = b[0] * b[0] + b[1] * b[1];
    if (da !== db) return da - db;
    if (a[0] !== b[0]) return a[0] - b[0];
    return a[1] - b[1];
  });
  return sorted.slice(0, k);
}
const kClosest = solve;
class Solution { kClosest(points, k) { return solve(points, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kClosest };
