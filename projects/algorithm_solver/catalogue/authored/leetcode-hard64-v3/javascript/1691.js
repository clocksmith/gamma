'use strict';

// 1691. Maximum Height by Stacking Cuboids: canonical orientations and dominance DP; O(n^2) time and O(n) space. Inputs are preserved.

function solve(cuboids) {
  const ordered = cuboids.map(cuboid => cuboid.slice().sort((a, b) => a - b));
  ordered.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  const height = ordered.map(cuboid => cuboid[2]);
  let answer = 0;
  for (let bottom = 0; bottom < ordered.length; bottom += 1) {
    for (let top = 0; top < bottom; top += 1) {
      if (ordered[top][0] <= ordered[bottom][0] && ordered[top][1] <= ordered[bottom][1] && ordered[top][2] <= ordered[bottom][2]) {
        height[bottom] = Math.max(height[bottom], height[top] + ordered[bottom][2]);
      }
    }
    answer = Math.max(answer, height[bottom]);
  }
  return answer;
}

const maxHeight = solve;
class Solution {
  maxHeight(cuboids) { return solve(cuboids); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxHeight };
