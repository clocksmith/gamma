'use strict';

// 91. Decode Ways (Medium).
// Specification: https://leetcode.com/problems/decode-ways/description/
function solve(s) {
  if (s[0] === '0') return 0;
  let previous = 1; let current = 1;
  for (let i = 1; i < s.length; i++) {
    let next = 0;
    if (s[i] !== '0') next += current;
    const two = Number(s.slice(i - 1, i + 1));
    if (two >= 10 && two <= 26) next += previous;
    previous = current; current = next;
  }
  return current;
}
const numDecodings = solve;
class Solution { numDecodings(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDecodings };
