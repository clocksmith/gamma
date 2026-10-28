'use strict';

// 1942. The Number of the Smallest Unoccupied Chair (Medium).
// Specification: https://leetcode.com/problems/the-number-of-the-smallest-unoccupied-chair/description/
function solve(times, targetFriend) {
  const order = times.map((t, i) => i).sort((a, b) => times[a][0] - times[b][0]);
  let occupied = []; let free = []; let nextChair = 0;
  for (const i of order) {
    const arrival = times[i][0]; const departure = times[i][1];
    const still = [];
    for (const occ of occupied) {
      if (occ[0] <= arrival) free.push(occ[1]); else still.push(occ);
    }
    occupied = still;
    free.sort((a, b) => a - b);
    let chair;
    if (free.length > 0) chair = free.shift(); else chair = nextChair++;
    if (i === targetFriend) return chair;
    occupied.push([departure, chair]);
  }
  return -1;
}
const smallestChair = solve;
class Solution { smallestChair(times, targetFriend) { return solve(times, targetFriend); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestChair };
