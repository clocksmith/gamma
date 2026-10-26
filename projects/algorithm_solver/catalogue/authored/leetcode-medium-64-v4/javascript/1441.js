'use strict';

// 1441. Build an Array With Stack Operations: emit pushes for the stream and pops for values absent from the target.
// O(target[-1]) time and O(target[-1]) space including the result; inputs are read-only.
function solve(target, n) {
  const result = [];
  let value = 1;
  for (const wanted of target) {
    while (value < wanted) {
      result.push('Push', 'Pop');
      value += 1;
    }
    result.push('Push');
    value += 1;
  }
  return result;
}

const buildArray = solve;
class Solution {
  buildArray(target, n) { return solve(target, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buildArray };
