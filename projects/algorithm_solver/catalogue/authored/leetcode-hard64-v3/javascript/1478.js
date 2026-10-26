'use strict';

// 1478. Allocate Mailboxes: median interval costs and partition DP; O(k*n^2) time and O(n^2) space.

function solve(houses, k) {
  const positions = houses.slice().sort((a, b) => a - b);
  const size = positions.length;
  if (k >= size) return 0;
  const cost = Array.from({ length: size }, () => Array(size).fill(0));
  for (let width = 2; width <= size; width += 1) {
    for (let left = 0; left + width <= size; left += 1) {
      const right = left + width - 1;
      cost[left][right] = positions[right] - positions[left];
      if (width > 2) cost[left][right] += cost[left + 1][right - 1];
    }
  }
  let previous = Array(size + 1).fill(Infinity);
  previous[0] = 0;
  for (let groups = 1; groups <= k; groups += 1) {
    const current = Array(size + 1).fill(Infinity);
    for (let covered = groups; covered <= size; covered += 1) {
      for (let split = groups - 1; split < covered; split += 1) {
        current[covered] = Math.min(current[covered], previous[split] + cost[split][covered - 1]);
      }
    }
    previous = current;
  }
  return previous[size];
}

const minDistance = solve;
class Solution {
  minDistance(houses, k) { return solve(houses, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDistance };
