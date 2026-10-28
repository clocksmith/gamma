'use strict';

// 1177. Can Make Palindrome from Substring (Medium).
// Specification: https://leetcode.com/problems/can-make-palindrome-from-substring/description/
function solve(s, queries) {
  const prefix = [new Array(26).fill(0)];
  const counts = new Array(26).fill(0);
  for (let i = 0; i < s.length; i++) {
    counts[s.charCodeAt(i) - 97]++;
    prefix.push(counts.slice());
  }
  const result = [];
  for (const [left, right, k] of queries) {
    let odd = 0;
    for (let letter = 0; letter < 26; letter++) { if ((prefix[right + 1][letter] - prefix[left][letter]) % 2 === 1) odd++; }
    result.push(Math.floor(odd / 2) <= k);
  }
  return result;
}
const canMakePaliQueries = solve;
class Solution { canMakePaliQueries(s, queries) { return solve(s, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMakePaliQueries };
