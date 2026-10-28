'use strict';

// 787. Cheapest Flights Within K Stops (Medium).
// Specification: https://leetcode.com/problems/cheapest-flights-within-k-stops/description/
function solve(n, flights, src, dst, k) {
  let dist = new Array(n).fill(Infinity);
  dist[src] = 0;
  for (let step = 0; step <= k; step++) {
    const next = dist.slice();
    for (const [from, to, price] of flights) {
      if (dist[from] !== Infinity) next[to] = Math.min(next[to], dist[from] + price);
    }
    dist = next;
  }
  return dist[dst] === Infinity ? -1 : dist[dst];
}
const findCheapestPrice = solve;
class Solution { findCheapestPrice(n, flights, src, dst, k) { return solve(n, flights, src, dst, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findCheapestPrice };
