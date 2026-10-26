'use strict';

// 2646. Minimize the Total Price of the Trips. Count path visits, then choose a minimum-cost independent set of discounts; O(n*(t+1)) time and O(n) space. Inputs are preserved.

function solve(n, edges, price, trips) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = Array(n).fill(-1);
  const depth = Array(n).fill(0);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      depth[neighbor] = depth[node] + 1;
      order.push(neighbor);
    }
  }
  const visits = Array(n).fill(0);
  for (const trip of trips) {
    let [first, second] = trip;
    while (first !== second) {
      if (depth[first] >= depth[second]) { visits[first] += 1; first = parent[first]; }
      else { visits[second] += 1; second = parent[second]; }
    }
    visits[first] += 1;
  }
  const full = visits.map((count, node) => count * price[node]);
  const half = visits.map((count, node) => count * Math.floor(price[node] / 2));
  for (let index = order.length - 1; index > 0; index -= 1) {
    const node = order[index];
    const previous = parent[node];
    full[previous] += Math.min(full[node], half[node]);
    half[previous] += full[node];
  }
  return Math.min(full[0], half[0]);
}

const minimumTotalPrice = solve;
class Solution {
  minimumTotalPrice(n, edges, price, trips) { return solve(n, edges, price, trips); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTotalPrice };
