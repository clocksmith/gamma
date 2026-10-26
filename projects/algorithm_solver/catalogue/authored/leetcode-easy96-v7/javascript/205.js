'use strict';

// 205. Isomorphic Strings (Easy).
// Specification: https://leetcode.com/problems/isomorphic-strings/description/
// O(n) time, O(a) space for distinct characters; enforce a bijection on ASCII input.
function solve(s, t) {
  if (s.length !== t.length) return false;
  const forward = new Map();
  const backward = new Map();
  for (let index = 0; index < s.length; index++) {
    const first = s[index];
    const second = t[index];
    if (forward.has(first) && forward.get(first) !== second) return false;
    if (backward.has(second) && backward.get(second) !== first) return false;
    forward.set(first, second);
    backward.set(second, first);
  }
  return true;
}

const isIsomorphic = solve;
class Solution {
  isIsomorphic(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isIsomorphic };
