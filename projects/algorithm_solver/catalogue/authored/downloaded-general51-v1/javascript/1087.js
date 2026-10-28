'use strict';

// 1087. Brace Expansion (Medium).
// Specification: https://leetcode.com/problems/brace-expansion/description/
function solve(s) {
  const groups = [];
  let index = 0;
  while (index < s.length) {
    if (s[index] === '{') {
      const end = s.indexOf('}', index);
      groups.push(s.slice(index + 1, end).split(',').sort());
      index = end + 1;
    } else { groups.push([s[index]]); index++; }
  }
  let result = [''];
  for (const group of groups) {
    const next = [];
    for (const prefix of result) { for (const ch of group) next.push(prefix + ch); }
    result = next;
  }
  return result.sort();
}
const expand = solve;
class Solution { expand(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, expand };
