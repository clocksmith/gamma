'use strict';

// 1560. Most Visited Sector in a Circular Track (Easy).
// Specification: https://leetcode.com/problems/most-visited-sector-in-a-circular-track/description/
// O(n) time, O(n) output space; complete laps affect all sectors equally.
function solve(n, rounds) {
  const start = rounds[0];
  const finish = rounds[rounds.length - 1];
  const result = [];
  for (let sector = 1; sector <= n; sector++) {
    const mostVisited = start <= finish
      ? sector >= start && sector <= finish
      : sector >= start || sector <= finish;
    if (mostVisited) result.push(sector);
  }
  return result;
}

const mostVisited = solve;
class Solution {
  mostVisited(n, rounds) { return solve(n, rounds); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostVisited };
