'use strict';

// 1318. Minimum Flips to Make a OR b Equal to c: count required changes independently at each bit.
// O(log(max(a, b, c) + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(a, b, c) {
  let answer = 0;
  while (a !== 0 || b !== 0 || c !== 0) {
    const first = a & 1;
    const second = b & 1;
    if ((c & 1) !== 0) {
      if (first === 0 && second === 0) answer += 1;
    } else answer += first + second;
    a >>>= 1;
    b >>>= 1;
    c >>>= 1;
  }
  return answer;
}

const minFlips = solve;
class Solution {
  minFlips(a, b, c) { return solve(a, b, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
