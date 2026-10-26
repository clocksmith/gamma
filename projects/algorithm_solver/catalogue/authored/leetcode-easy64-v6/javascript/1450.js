'use strict';

// 1450. Number of Students Doing Homework at a Given Time (Easy).
// Specification: https://leetcode.com/problems/number-of-students-doing-homework-at-a-given-time/description/
// O(n) time, O(1) space; interval endpoints are inclusive; preserve inputs.
function solve(startTime, endTime, queryTime) {
  let result = 0;
  for (let index = 0; index < startTime.length; index++) {
    if (startTime[index] <= queryTime && queryTime <= endTime[index]) result++;
  }
  return result;
}

const busyStudent = solve;
class Solution {
  busyStudent(startTime, endTime, queryTime) { return solve(startTime, endTime, queryTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, busyStudent };
