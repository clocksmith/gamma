'use strict';

// 1061. Lexicographically Smallest Equivalent String (Medium).
// Specification: https://leetcode.com/problems/lexicographically-smallest-equivalent-string/description/
function solve(s1, s2, baseStr) {
  const parent = [];
  for (let i = 0; i < 26; i++) parent.push(i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  function union(a, b) {
    const rootA = find(a); const rootB = find(b);
    if (rootA !== rootB) parent[Math.max(rootA, rootB)] = Math.min(rootA, rootB);
  }
  for (let i = 0; i < s1.length; i++) union(s1.charCodeAt(i) - 97, s2.charCodeAt(i) - 97);
  let result = '';
  for (const ch of baseStr) result += String.fromCharCode(97 + find(ch.charCodeAt(0) - 97));
  return result;
}
const smallestEquivalentString = solve;
class Solution { smallestEquivalentString(s1, s2, baseStr) { return solve(s1, s2, baseStr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestEquivalentString };
