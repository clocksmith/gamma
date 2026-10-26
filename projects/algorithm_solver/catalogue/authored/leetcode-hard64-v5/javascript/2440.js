'use strict';

// 2440. Create Components With Same Value. Try divisor component sums and greedily close subtrees in postorder; O(sqrt(S)+n*tau(S)+tau(S) log tau(S)) time and O(n+tau(S)) space, S=sum(nums). Inputs are preserved.

function solve(nums, edges) {
  const size = nums.length;
  const graph = Array.from({ length: size }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = Array(size).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      order.push(neighbor);
    }
  }
  let total = 0;
  let largest = 0;
  for (const value of nums) { total += value; largest = Math.max(largest, value); }
  const targets = new Set();
  for (let divisor = 1; divisor * divisor <= total; divisor += 1) {
    if (total % divisor === 0) { targets.add(divisor); targets.add(total / divisor); }
  }
  for (const target of Array.from(targets).sort((a, b) => a - b)) {
    if (target < largest || total / target > size) continue;
    const remaining = nums.slice();
    let feasible = true;
    for (let index = order.length - 1; index >= 0; index -= 1) {
      const node = order[index];
      if (remaining[node] > target) { feasible = false; break; }
      if (remaining[node] === target) remaining[node] = 0;
      if (parent[node] !== -1) remaining[parent[node]] += remaining[node];
    }
    if (feasible && remaining[0] === 0) return total / target - 1;
  }
  return 0;
}

const componentValue = solve;
class Solution {
  componentValue(nums, edges) { return solve(nums, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, componentValue };
