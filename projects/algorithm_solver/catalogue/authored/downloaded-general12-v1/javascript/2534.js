'use strict';

// 2534. Time Taken to Cross the Door (Hard).
// Specification: https://leetcode.com/problems/time-taken-to-cross-the-door/description/
function solve(arrival, state) {
  const n = arrival.length;
  const q = [[], []];
  const head = [0, 0];
  const ans = new Array(n).fill(0);
  let t = 0; let i = 0; let st = 1;
  const size = (d) => q[d].length - head[d];
  while (i < n || size(0) > 0 || size(1) > 0) {
    while (i < n && arrival[i] <= t) { q[state[i]].push(i); i++; }
    if (size(0) > 0 && size(1) > 0) {
      ans[q[st][head[st]++]] = t;
    } else if (size(0) > 0 || size(1) > 0) {
      st = size(0) > 0 ? 0 : 1;
      ans[q[st][head[st]++]] = t;
    } else {
      st = 1;
    }
    t++;
  }
  return ans;
}
const timeTaken = solve;
class Solution { timeTaken(arrival, state) { return solve(arrival, state); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, timeTaken };
