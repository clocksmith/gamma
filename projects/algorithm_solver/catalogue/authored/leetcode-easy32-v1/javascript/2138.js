'use strict';

// 2138. Divide a String Into Groups of Size k (Easy).
// Specification: https://leetcode.com/problems/divide-a-string-into-groups-of-size-k/description/
// O(n + k) time and output space. Only the last group may need padding.
function solve(s, k, fill) {
  const result = [];
  for (let start = 0; start < s.length; start += k) {
    const group = s.slice(start, start + k);
    result.push(group + fill.repeat(k - group.length));
  }
  return result;
}

const divideString = solve;
class Solution {
  divideString(s, k, fill) { return solve(s, k, fill); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, divideString };
