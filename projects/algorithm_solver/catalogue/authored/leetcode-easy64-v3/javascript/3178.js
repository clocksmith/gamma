'use strict';

// 3178. Find the Child Who Has the Ball After K Seconds (Easy).
// Specification: https://leetcode.com/problems/find-the-child-who-has-the-ball-after-k-seconds/description/
// O(1) time and space; reflect the position over a period of 2 * (n - 1).
function solve(n, k) {
  const distance = n - 1;
  const phase = k % (2 * distance);
  return phase <= distance ? phase : 2 * distance - phase;
}

const numberOfChild = solve;
class Solution {
  numberOfChild(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfChild };
