'use strict';

// 551. Student Attendance Record I (Easy).
// Specification: https://leetcode.com/problems/student-attendance-record-i/description/
// O(n) time, O(1) space; reject two absences or three consecutive late days.
function solve(s) {
  let absences = 0;
  let lateRun = 0;
  for (const character of s) {
    if (character === 'A') absences++;
    lateRun = character === 'L' ? lateRun + 1 : 0;
    if (absences >= 2 || lateRun >= 3) return false;
  }
  return true;
}

const checkRecord = solve;
class Solution {
  checkRecord(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkRecord };
