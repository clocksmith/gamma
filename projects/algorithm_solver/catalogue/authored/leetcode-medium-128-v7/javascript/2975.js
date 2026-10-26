'use strict';

// 2975. Maximum Square Area by Removing Fences From a Field: intersect attainable horizontal and vertical distances and square the largest exactly.
// O(h * h + v * v) expected time and O(h * h + v) auxiliary space; inputs are read-only.
function solve(m, n, hFences, vFences) {
  const horizontal = [1, m, ...hFences];
  const vertical = [1, n, ...vFences];
  const distances = new Set();
  for (let right = 0; right < horizontal.length; right += 1) {
    for (let left = 0; left < right; left += 1) distances.add(Math.abs(horizontal[right] - horizontal[left]));
  }
  let best = 0;
  for (let right = 0; right < vertical.length; right += 1) {
    for (let left = 0; left < right; left += 1) {
      const distance = Math.abs(vertical[right] - vertical[left]);
      if (distances.has(distance)) best = Math.max(best, distance);
    }
  }
  return best > 0 ? Number(BigInt(best) * BigInt(best) % 1000000007n) : -1;
}

const maximizeSquareArea = solve;
class Solution {
  maximizeSquareArea(m, n, hFences, vFences) { return solve(m, n, hFences, vFences); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeSquareArea };
