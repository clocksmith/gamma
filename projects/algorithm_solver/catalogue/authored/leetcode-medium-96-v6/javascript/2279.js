'use strict';

// 2279. Maximum Bags With Full Capacity of Rocks: fill bags in ascending order of their remaining capacity.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(capacity, rocks, additionalRocks) {
  const needed = capacity.map((limit, index) => limit - rocks[index]);
  needed.sort((left, right) => left - right);
  let remaining = additionalRocks;
  let full = 0;
  for (const amount of needed) {
    if (amount > remaining) break;
    remaining -= amount;
    full += 1;
  }
  return full;
}

const maximumBags = solve;
class Solution {
  maximumBags(capacity, rocks, additionalRocks) { return solve(capacity, rocks, additionalRocks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBags };
