'use strict';

// 2167. Minimum Time to Remove All Cars Containing Illegal Goods. Optimal prefix removals plus a suffix cut; O(n) time and O(1) space. Inputs are preserved.

function solve(s) {
  let prefix = 0;
  let answer = s.length;
  for (let index = 0; index < s.length; index += 1) {
    if (s[index] === '1') prefix = Math.min(prefix + 2, index + 1);
    answer = Math.min(answer, prefix + s.length - index - 1);
  }
  return answer;
}

const minimumTime = solve;
class Solution {
  minimumTime(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
