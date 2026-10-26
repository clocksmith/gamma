'use strict';

// 1436. Destination City (Easy).
// Specification: https://leetcode.com/problems/destination-city/description/
// O(n) expected set operations, O(n) space; preserve paths and its rows.
function solve(paths) {
  const departures = new Set();
  for (const path of paths) departures.add(path[0]);
  for (const path of paths) {
    if (!departures.has(path[1])) return path[1];
  }
  return '';
}

const destCity = solve;
class Solution {
  destCity(paths) { return solve(paths); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, destCity };
