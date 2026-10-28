'use strict';

// 3210. Find the Encrypted String (Easy).
// Specification: https://leetcode.com/problems/find-the-encrypted-string/description/
function solve(s, k) {
  const n = s.length; let out = '';
  for (let i = 0; i < n; i++) out += s[(i + k) % n];
  return out;
}
const getEncryptedString = solve;
class Solution { getEncryptedString(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getEncryptedString };
