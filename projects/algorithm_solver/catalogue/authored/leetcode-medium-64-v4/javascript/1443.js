'use strict';

// 1443. Minimum Time to Collect All Apples in a Tree: propagate apple requirements toward the root in reverse traversal order.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, edges, hasApple) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const child of graph[node]) {
      if (child !== parent[node]) {
        parent[child] = node;
        order.push(child);
      }
    }
  }
  const needed = hasApple.slice();
  let total = 0;
  for (let index = n - 1; index > 0; index -= 1) {
    const node = order[index];
    if (needed[node]) {
      total += 2;
      needed[parent[node]] = true;
    }
  }
  return total;
}

const minTime = solve;
class Solution {
  minTime(n, edges, hasApple) { return solve(n, edges, hasApple); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTime };
