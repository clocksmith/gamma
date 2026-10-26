'use strict';

// 252. Meeting Rooms (Easy).
// Specification: https://leetcode.com/problems/meeting-rooms/description/
// O(n log n) time, O(n) space; compare adjacent sorted intervals without mutating input.
function solve(intervals) {
  const ordered = intervals.slice().sort((a, b) => a[0] - b[0]);
  for (let index = 1; index < ordered.length; index++) {
    if (ordered[index][0] < ordered[index - 1][1]) return false;
  }
  return true;
}

const canAttendMeetings = solve;
class Solution {
  canAttendMeetings(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canAttendMeetings };
