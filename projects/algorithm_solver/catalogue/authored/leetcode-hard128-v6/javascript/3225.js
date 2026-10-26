'use strict';

// 3225. Maximum Score From Grid Operations.
// Track adjacent black-prefix heights and optimize the earlier height with prefix/suffix maxima; O(n^3) time and O(n^2) space. Inputs are preserved.

function solve(grid) {
  const n = grid.length;
  let best = Array.from({ length: n + 1 }, () => Array(n + 1).fill(-Infinity));
  best[0].fill(0);
  for (let column = 1; column < n; column += 1) {
    const prefix = [0];
    for (let row = 0; row < n; row += 1) prefix.push(prefix[row] + grid[row][column - 1]);
    const following = Array.from({ length: n + 1 }, () => Array(n + 1).fill(-Infinity));
    for (let middle = 0; middle <= n; middle += 1) {
      const leftMaximum = Array(n + 1).fill(-Infinity), rightMaximum = Array(n + 2).fill(-Infinity);
      for (let earlier = 0; earlier <= n; earlier += 1) {
        leftMaximum[earlier] = Math.max(earlier ? leftMaximum[earlier - 1] : -Infinity, best[earlier][middle]);
      }
      for (let earlier = n; earlier >= 0; earlier -= 1) {
        rightMaximum[earlier] = Math.max(rightMaximum[earlier + 1], best[earlier][middle] + Math.max(0, prefix[earlier] - prefix[middle]));
      }
      for (let later = 0; later <= n; later += 1) {
        following[middle][later] = Math.max(leftMaximum[later] + Math.max(0, prefix[later] - prefix[middle]), rightMaximum[later + 1]);
      }
    }
    best = following;
  }
  const prefix = [0];
  for (let row = 0; row < n; row += 1) prefix.push(prefix[row] + grid[row][n - 1]);
  let answer = 0;
  for (let earlier = 0; earlier <= n; earlier += 1) {
    for (let last = 0; last <= n; last += 1) answer = Math.max(answer, best[earlier][last] + Math.max(0, prefix[earlier] - prefix[last]));
  }
  return answer;
}

const maximumScore = solve;
class Solution {
  maximumScore(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
