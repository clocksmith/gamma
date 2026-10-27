'use strict';

// 624. Maximum Distance in Arrays. Compare each array against extrema from previous arrays only.

function solve(arrays) {
  let minimum = arrays[0][0], maximum = arrays[0][arrays[0].length - 1], answer = 0;
  for (let i = 1; i < arrays.length; i += 1) {
    const row = arrays[i];
    answer = Math.max(answer, Math.abs(row[row.length - 1] - minimum), Math.abs(maximum - row[0]));
    minimum = Math.min(minimum, row[0]); maximum = Math.max(maximum, row[row.length - 1]);
  }
  return answer;
}

const maxDistance = solve;
class Solution {
  maxDistance(arrays) { return solve(arrays); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
