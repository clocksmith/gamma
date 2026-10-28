'use strict';

// 1209. Remove All Adjacent Duplicates in String II (Medium).
// Specification: https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string-ii/description/
function solve(s, k) {
  const stack = [];
  for (const ch of s) {
    if (stack.length > 0 && stack[stack.length - 1][0] === ch) stack[stack.length - 1][1]++;
    else stack.push([ch, 1]);
    if (stack[stack.length - 1][1] === k) stack.pop();
  }
  return stack.map(([ch, count]) => ch.repeat(count)).join('');
}
const removeDuplicates = solve;
class Solution { removeDuplicates(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
