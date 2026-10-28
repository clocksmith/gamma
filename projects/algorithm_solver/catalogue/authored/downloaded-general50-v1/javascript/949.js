'use strict';

// 949. Largest Time for Given Digits (Medium).
// Specification: https://leetcode.com/problems/largest-time-for-given-digits/description/
function solve(arr) {
  let best = -1;
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      if (j === i) continue;
      for (let k = 0; k < 4; k++) {
        if (k === i || k === j) continue;
        for (let l = 0; l < 4; l++) {
          if (l === i || l === j || l === k) continue;
          const hour = arr[i] * 10 + arr[j];
          const minute = arr[k] * 10 + arr[l];
          if (hour < 24 && minute < 60) best = Math.max(best, hour * 60 + minute);
        }
      }
    }
  }
  if (best === -1) return '';
  const hour = String(Math.floor(best / 60)).padStart(2, '0');
  const minute = String(best % 60).padStart(2, '0');
  return hour + ':' + minute;
}
const largestTimeFromDigits = solve;
class Solution { largestTimeFromDigits(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestTimeFromDigits };
