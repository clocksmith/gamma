'use strict';

// 791. Custom Sort String (Medium).
// Specification: https://leetcode.com/problems/custom-sort-string/description/
function solve(order, s) {
  const rank = {};
  for (let i = 0; i < order.length; i++) rank[order[i]] = i;
  const ordered = [];
  const rest = [];
  for (const ch of s) { if (ch in rank) ordered.push(ch); else rest.push(ch); }
  ordered.sort((a, b) => rank[a] - rank[b]);
  return ordered.join('') + rest.join('');
}
const customSortString = solve;
class Solution { customSortString(order, s) { return solve(order, s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, customSortString };
