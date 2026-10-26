'use strict';

// 2446. Determine if Two Events Have Conflict (Easy).
// Specification: https://leetcode.com/problems/determine-if-two-events-have-conflict/description/
// O(1) time and space; zero-padded HH:MM strings compare chronologically; endpoints are inclusive.
function solve(event1, event2) {
  return event1[0] <= event2[1] && event2[0] <= event1[1];
}

const haveConflict = solve;
class Solution {
  haveConflict(event1, event2) { return solve(event1, event2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, haveConflict };
