'use strict';

// 2463. Minimum Total Distance Traveled. Assign consecutive sorted robots to each sorted factory; O(F log F+R log R+F*R^2) time and O(F+R) space. Inputs are preserved.

function solve(robot, factory) {
  const robots = robot.slice().sort((a, b) => a - b);
  const factories = factory.slice().sort((a, b) => a[0] - b[0]);
  const size = robots.length;
  let best = Array(size + 1).fill(Infinity);
  best[0] = 0;
  for (const [position, capacity] of factories) {
    const current = best.slice();
    for (let repaired = 1; repaired <= size; repaired += 1) {
      let distance = 0;
      for (let taken = 1; taken <= Math.min(capacity, repaired); taken += 1) {
        distance += Math.abs(robots[repaired - taken] - position);
        current[repaired] = Math.min(current[repaired], best[repaired - taken] + distance);
      }
    }
    best = current;
  }
  return best[size];
}

const minimumTotalDistance = solve;
class Solution {
  minimumTotalDistance(robot, factory) { return solve(robot, factory); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTotalDistance };
