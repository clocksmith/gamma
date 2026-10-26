'use strict';

// 2477. Minimum Fuel Cost to Report to the Capital: aggregate representatives in iterative postorder and charge full cars across each edge.
// O(n) time and O(n) auxiliary space for n tree vertices; inputs are read-only.
function solve(roads, seats) {
  const size = roads.length + 1;
  const graph = Array.from({ length: size }, () => []);
  for (const [left, right] of roads) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = new Int32Array(size).fill(-1);
  const order = [0];
  for (let head = 0; head < order.length; head += 1) {
    const node = order[head];
    for (const neighbor of graph[node]) {
      if (neighbor !== parent[node]) {
        parent[neighbor] = node;
        order.push(neighbor);
      }
    }
  }
  const people = new Array(size).fill(1);
  let fuel = 0;
  for (let index = order.length - 1; index > 0; index -= 1) {
    const node = order[index];
    fuel += Math.floor((people[node] + seats - 1) / seats);
    people[parent[node]] += people[node];
  }
  return fuel;
}

const minimumFuelCost = solve;
class Solution {
  minimumFuelCost(roads, seats) { return solve(roads, seats); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumFuelCost };
