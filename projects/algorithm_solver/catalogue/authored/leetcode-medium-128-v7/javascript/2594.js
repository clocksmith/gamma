'use strict';

// 2594. Minimum Time to Repair Cars: binary search time using exact integer repair capacities grouped by rank.
// O(n + u log T) time and O(u) auxiliary space, where T is the search bound and u is the number of ranks; inputs are read-only.
function solve(ranks, cars) {
  const counts = new Map();
  let minimumRank = ranks[0];
  for (const rank of ranks) {
    counts.set(rank, (counts.get(rank) || 0) + 1);
    minimumRank = Math.min(minimumRank, rank);
  }
  let low = 0;
  let high = minimumRank * cars * cars;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let repaired = 0;
    for (const [rank, count] of counts) {
      const budget = Math.floor(middle / rank);
      let capacity = Math.floor(Math.sqrt(budget));
      while ((capacity + 1) * (capacity + 1) <= budget) capacity += 1;
      while (capacity * capacity > budget) capacity -= 1;
      repaired += capacity * count;
      if (repaired >= cars) break;
    }
    if (repaired >= cars) high = middle;
    else low = middle + 1;
  }
  return low;
}

const repairCars = solve;
class Solution {
  repairCars(ranks, cars) { return solve(ranks, cars); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, repairCars };
