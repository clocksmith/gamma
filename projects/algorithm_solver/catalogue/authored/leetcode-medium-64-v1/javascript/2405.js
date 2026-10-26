'use strict';

// 2405. Optimal Partition of String: start a new partition exactly when the next letter repeats in the current one.
// O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only.
function solve(s) {
  if (s.length === 0) return 0;
  let mask = 0;
  let answer = 1;
  for (let index = 0; index < s.length; index += 1) {
    const bit = 1 << (s.charCodeAt(index) - 97);
    if (mask & bit) {
      answer += 1;
      mask = 0;
    }
    mask |= bit;
  }
  return answer;
}

const partitionString = solve;
class Solution {
  partitionString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, partitionString };
