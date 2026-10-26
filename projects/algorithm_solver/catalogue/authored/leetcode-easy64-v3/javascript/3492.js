'use strict';

// 3492. Maximum Containers on a Ship (Easy).
// Specification: https://leetcode.com/problems/maximum-containers-on-a-ship/description/
// O(1) time and space; both deck area and integer weight capacity limit the count.
function solve(n, w, maxWeight) {
  return Math.min(n * n, Math.floor(maxWeight / w));
}

const maxContainers = solve;
class Solution {
  maxContainers(n, w, maxWeight) { return solve(n, w, maxWeight); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxContainers };
