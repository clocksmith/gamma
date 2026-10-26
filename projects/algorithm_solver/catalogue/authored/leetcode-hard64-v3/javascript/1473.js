'use strict';

// 1473. Paint House III: neighborhood DP with two minima per prior layer; O(m*n*target) time and O(n*target) space.

function solve(houses, cost, m, n, target) {
  let previous = Array.from({ length: target + 1 }, () => Array(n + 1).fill(Infinity));
  previous[0][0] = 0;
  for (let index = 0; index < houses.length; index += 1) {
    const current = Array.from({ length: target + 1 }, () => Array(n + 1).fill(Infinity));
    for (let groups = 1; groups <= Math.min(target, index + 1); groups += 1) {
      let first = Infinity;
      let second = Infinity;
      let firstColor = -1;
      for (let color = 0; color <= n; color += 1) {
        const value = previous[groups - 1][color];
        if (value < first) {
          second = first;
          first = value;
          firstColor = color;
        } else if (value < second) second = value;
      }
      for (let color = 1; color <= n; color += 1) {
        if (houses[index] !== 0 && houses[index] !== color) continue;
        const different = color === firstColor ? second : first;
        const price = houses[index] === 0 ? cost[index][color - 1] : 0;
        current[groups][color] = Math.min(previous[groups][color], different) + price;
      }
    }
    previous = current;
  }
  const answer = Math.min(...previous[target]);
  return answer === Infinity ? -1 : answer;
}

const minCost = solve;
class Solution {
  minCost(houses, cost, m, n, target) { return solve(houses, cost, m, n, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
