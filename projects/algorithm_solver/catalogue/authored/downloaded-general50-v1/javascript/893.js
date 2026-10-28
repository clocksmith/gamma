'use strict';

// 893. Groups of Special-Equivalent Strings (Medium).
// Specification: https://leetcode.com/problems/groups-of-special-equivalent-strings/description/
function solve(words) {
  const groups = new Set();
  for (const word of words) {
    let even = ''; let odd = '';
    for (let i = 0; i < word.length; i++) { if (i % 2 === 0) even += word[i]; else odd += word[i]; }
    groups.add([...even].sort().join('') + '|' + [...odd].sort().join(''));
  }
  return groups.size;
}
const numSpecialEquivGroups = solve;
class Solution { numSpecialEquivGroups(words) { return solve(words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSpecialEquivGroups };
