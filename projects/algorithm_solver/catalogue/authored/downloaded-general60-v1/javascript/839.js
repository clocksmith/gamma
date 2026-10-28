'use strict';

// 839. Similar String Groups (Hard).
// Specification: https://leetcode.com/problems/similar-string-groups/description/
function solve(strs) {
  const n = strs.length;
  const parent = Array.from({ length: n }, (_, i) => i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  function union(a, b) { const ra = find(a); const rb = find(b); if (ra !== rb) parent[ra] = rb; }
  function similar(a, b) {
    let diff = 0;
    for (let i = 0; i < a.length; i++) { if (a[i] !== b[i]) { diff++; if (diff > 2) return false; } }
    return true;
  }
  for (let i = 0; i < n; i++) { for (let j = i + 1; j < n; j++) { if (similar(strs[i], strs[j])) union(i, j); } }
  const groups = new Set();
  for (let i = 0; i < n; i++) groups.add(find(i));
  return groups.size;
}
const numSimilarGroups = solve;
class Solution { numSimilarGroups(strs) { return solve(strs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSimilarGroups };
