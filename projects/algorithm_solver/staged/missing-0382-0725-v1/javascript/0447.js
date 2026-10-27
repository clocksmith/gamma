'use strict';

// 447. Number of Boomerangs.

function solve(points) {
  let answer = 0;
  for (const [x, y] of points) {
    const counts = new Map();
    for (const [a, b] of points) {
      const distance = (x - a) ** 2 + (y - b) ** 2;
      counts.set(distance, (counts.get(distance) || 0) + 1);
    }
    for (const count of counts.values()) answer += count * (count - 1);
  }
  return answer;
}

const numberOfBoomerangs = solve;
class Solution {
  numberOfBoomerangs(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfBoomerangs };
