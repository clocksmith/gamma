'use strict';

// 1167. Minimum Cost to Connect Sticks (Medium).
// Specification: https://leetcode.com/problems/minimum-cost-to-connect-sticks/description/
function solve(sticks) {
  const heap = sticks.slice().sort((a, b) => a - b);
  let total = 0;
  while (heap.length > 1) {
    const first = heap.shift(); const second = heap.shift();
    const cost = first + second; total += cost;
    let inserted = false;
    for (let i = 0; i < heap.length; i++) { if (cost <= heap[i]) { heap.splice(i, 0, cost); inserted = true; break; } }
    if (!inserted) heap.push(cost);
  }
  return total;
}
const connectSticks = solve;
class Solution { connectSticks(sticks) { return solve(sticks); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, connectSticks };
