'use strict';

// 1417. Reformat The String (Easy).
// Specification: https://leetcode.com/problems/reformat-the-string/description/
// O(n) time and space; alternate ASCII letters and digits, preserving within-type order.
function solve(s) {
  let first = [];
  let second = [];
  for (const character of s) {
    if (character >= '0' && character <= '9') second.push(character);
    else first.push(character);
  }
  if (Math.abs(first.length - second.length) > 1) return '';
  if (first.length < second.length) [first, second] = [second, first];
  const result = [];
  for (let index = 0; index < first.length; index++) {
    result.push(first[index]);
    if (index < second.length) result.push(second[index]);
  }
  return result.join('');
}

const reformat = solve;
class Solution {
  reformat(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reformat };
