'use strict';

// 38. Count and Say (Medium).
// Specification: https://leetcode.com/problems/count-and-say/description/
function solve(n) {
  let current = '1';
  for (let step = 1; step < n; step++) {
    let next = ''; let count = 1;
    for (let i = 0; i < current.length; i++) {
      if (i + 1 < current.length && current[i + 1] === current[i]) count++;
      else { next += String(count) + current[i]; count = 1; }
    }
    current = next;
  }
  return current;
}
const countAndSay = solve;
class Solution { countAndSay(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countAndSay };
