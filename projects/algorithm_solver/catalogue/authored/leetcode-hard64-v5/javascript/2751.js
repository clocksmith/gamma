'use strict';

// 2751. Robot Collisions. Resolve sorted encounters against a stack of right-moving robots; O(n log n) time and O(n) space. Inputs are preserved.

function solve(positions, healths, directions) {
  const remaining = healths.slice();
  const rightward = [];
  const order = Array.from({ length: positions.length }, (_, index) => index).sort((a, b) => positions[a] - positions[b]);
  for (const robot of order) {
    if (directions[robot] === 'R') { rightward.push(robot); continue; }
    while (rightward.length > 0 && remaining[robot] > 0) {
      const other = rightward[rightward.length - 1];
      if (remaining[other] < remaining[robot]) {
        remaining[other] = 0;
        remaining[robot] -= 1;
        rightward.pop();
      } else if (remaining[other] > remaining[robot]) {
        remaining[other] -= 1;
        remaining[robot] = 0;
      } else {
        remaining[other] = 0;
        remaining[robot] = 0;
        rightward.pop();
      }
    }
  }
  return remaining.filter(health => health > 0);
}

const survivedRobotsHealths = solve;
class Solution {
  survivedRobotsHealths(positions, healths, directions) { return solve(positions, healths, directions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, survivedRobotsHealths };
