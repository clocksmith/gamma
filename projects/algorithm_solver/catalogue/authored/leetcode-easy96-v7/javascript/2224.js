'use strict';

// 2224. Minimum Number of Operations to Convert Time (Easy).
// Specification: https://leetcode.com/problems/minimum-number-of-operations-to-convert-time/description/
// O(1) time and space; correct is not earlier than current; greedily use 60, 15, 5, 1 minutes.
function solve(current, correct) {
  function minutes(time) {
    return Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
  }
  let difference = minutes(correct) - minutes(current);
  let operations = 0;
  for (const step of [60, 15, 5, 1]) {
    operations += Math.floor(difference / step);
    difference %= step;
  }
  return operations;
}

const convertTime = solve;
class Solution {
  convertTime(current, correct) { return solve(current, correct); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertTime };
