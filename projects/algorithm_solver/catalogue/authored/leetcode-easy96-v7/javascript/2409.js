'use strict';

// 2409. Count Days Spent Together (Easy).
// Specification: https://leetcode.com/problems/count-days-spent-together/description/
// O(1) time and space for a non-leap year; compute the inclusive intersection of day-of-year intervals.
function solve(arriveAlice, leaveAlice, arriveBob, leaveBob) {
  const monthLengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  function dayOfYear(date) {
    const month = Number(date.slice(0, 2));
    let day = Number(date.slice(3));
    for (let index = 0; index < month - 1; index++) day += monthLengths[index];
    return day;
  }
  const start = Math.max(dayOfYear(arriveAlice), dayOfYear(arriveBob));
  const end = Math.min(dayOfYear(leaveAlice), dayOfYear(leaveBob));
  return Math.max(0, end - start + 1);
}

const countDaysTogether = solve;
class Solution {
  countDaysTogether(arriveAlice, leaveAlice, arriveBob, leaveBob) { return solve(arriveAlice, leaveAlice, arriveBob, leaveBob); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDaysTogether };
