'use strict';

// 2399. Check Distances Between Same Letters (Easy).
// Specification: https://leetcode.com/problems/check-distances-between-same-letters/description/
// O(n) time, O(1) alphabet space; each present letter occurs exactly twice.
function solve(s, distance) {
  const first = new Array(26).fill(-1);
  for (let index = 0; index < s.length; index++) {
    const letter = s.charCodeAt(index) - 97;
    if (first[letter] === -1) first[letter] = index;
    else if (index - first[letter] - 1 !== distance[letter]) return false;
  }
  return true;
}

const checkDistances = solve;
class Solution {
  checkDistances(s, distance) { return solve(s, distance); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkDistances };
