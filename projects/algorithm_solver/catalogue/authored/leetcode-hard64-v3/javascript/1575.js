'use strict';

// 1575. Count All Possible Routes: bottom-up remaining-fuel DP on distinct locations; O(fuel*n^2) time and O(fuel*n) space.

function solve(locations, start, finish, fuel) {
  const modulus = 1000000007;
  const size = locations.length;
  const ways = Array.from({ length: fuel + 1 }, () => Array(size).fill(0));
  for (let remaining = 0; remaining <= fuel; remaining += 1) {
    for (let city = 0; city < size; city += 1) {
      let count = city === finish ? 1 : 0;
      for (let neighbor = 0; neighbor < size; neighbor += 1) {
        if (neighbor === city) continue;
        const cost = Math.abs(locations[city] - locations[neighbor]);
        if (cost <= remaining) count = (count + ways[remaining - cost][neighbor]) % modulus;
      }
      ways[remaining][city] = count;
    }
  }
  return ways[fuel][start];
}

const countRoutes = solve;
class Solution {
  countRoutes(locations, start, finish, fuel) { return solve(locations, start, finish, fuel); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countRoutes };
