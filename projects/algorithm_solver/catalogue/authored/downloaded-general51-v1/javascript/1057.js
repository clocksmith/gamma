'use strict';

// 1057. Campus Bikes (Medium).
// Specification: https://leetcode.com/problems/campus-bikes/description/
function solve(workers, bikes) {
  const pairs = [];
  for (let w = 0; w < workers.length; w++) {
    for (let b = 0; b < bikes.length; b++) {
      const distance = Math.abs(workers[w][0] - bikes[b][0]) + Math.abs(workers[w][1] - bikes[b][1]);
      pairs.push([distance, w, b]);
    }
  }
  pairs.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  const answer = new Array(workers.length).fill(-1);
  const usedBikes = new Set();
  for (const [distance, w, b] of pairs) {
    if (answer[w] === -1 && !usedBikes.has(b)) { answer[w] = b; usedBikes.add(b); }
  }
  return answer;
}
const assignBikes = solve;
class Solution { assignBikes(workers, bikes) { return solve(workers, bikes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, assignBikes };
