'use strict';

// 3544. Subtree Inversion Sum.
// Bottom-up tree states track inherited sign and the remaining inversion cooldown; O(n*k) time and O(n*k) worst-case space. Inputs are preserved.

function solve(edges, nums, k) {
  const n = nums.length, graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) { graph[first].push(second); graph[second].push(first); }
  const parent = new Int32Array(n).fill(-1), order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const child of graph[node]) if (child !== parent[node]) { parent[child] = node; order.push(child); }
  }
  const states = Array(n).fill(null);
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index], current = new Float64Array(2 * k);
    current.fill(nums[node], 0, k); current.fill(-nums[node], k);
    let flipPositive = -nums[node], flipNegative = nums[node];
    for (const child of graph[node]) {
      if (child === parent[node]) continue;
      const other = states[child];
      flipPositive += other[2 * k - 1]; flipNegative += other[k - 1];
      for (let wait = 0; wait < k; wait += 1) {
        const following = Math.max(0, wait - 1);
        current[wait] += other[following]; current[k + wait] += other[k + following];
      }
      states[child] = null;
    }
    current[0] = Math.max(current[0], flipPositive); current[k] = Math.max(current[k], flipNegative);
    states[node] = current;
  }
  return states[0][0];
}

const subtreeInversionSum = solve;
class Solution {
  subtreeInversionSum(edges, nums, k) { return solve(edges, nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subtreeInversionSum };
