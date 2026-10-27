'use strict';

// 514. Freedom Trail.

function solve(ring, key) {
  const positions = new Map();
  for (let i = 0; i < ring.length; i += 1) {
    if (!positions.has(ring[i])) positions.set(ring[i], []);
    positions.get(ring[i]).push(i);
  }
  let costs = new Map([[0, 0]]);
  for (const char of key) {
    const next = new Map();
    for (const position of positions.get(char)) {
      let best = Infinity;
      for (const [previous, cost] of costs) {
        const difference = Math.abs(position - previous);
        best = Math.min(best, cost + Math.min(difference, ring.length - difference) + 1);
      }
      next.set(position, best);
    }
    costs = next;
  }
  let answer = Infinity;
  for (const cost of costs.values()) answer = Math.min(answer, cost);
  return answer;
}

const findRotateSteps = solve;
class Solution {
  findRotateSteps(ring, key) { return solve(ring, key); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRotateSteps };
