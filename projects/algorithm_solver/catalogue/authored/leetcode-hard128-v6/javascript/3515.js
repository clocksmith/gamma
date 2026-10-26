'use strict';

// 3515. Shortest Path in a Weighted Tree.
// Euler intervals turn edge-weight changes into subtree range additions and root-distance point queries; O(n+q log n) time and O(n+q) space. Inputs are preserved.

function solve(n, edges, queries) {
  const graph = Array.from({ length: n + 1 }, () => []);
  for (const [first, second, weight] of edges) { graph[first].push([second, weight]); graph[second].push([first, weight]); }
  const parent = new Int32Array(n + 1), edgeWeight = new Float64Array(n + 1), distance = new Float64Array(n + 1);
  const entry = new Int32Array(n + 1), leave = new Int32Array(n + 1), stack = [[1, 0, 0, false]];
  let timer = 0;
  while (stack.length) {
    const [node, predecessor, weight, exiting] = stack.pop();
    if (exiting) { leave[node] = timer; continue; }
    parent[node] = predecessor; edgeWeight[node] = weight; distance[node] = distance[predecessor] + weight;
    entry[node] = timer; timer += 1;
    stack.push([node, predecessor, weight, true]);
    for (const [child, childWeight] of graph[node]) if (child !== predecessor) stack.push([child, node, childWeight, false]);
  }
  const changes = new Float64Array(n + 1);
  function add(index, amount) {
    for (index += 1; index <= n; index += index & -index) changes[index] += amount;
  }
  const answers = [];
  for (const query of queries) {
    if (query[0] === 1) {
      const [, first, second, weight] = query, child = parent[first] === second ? first : second;
      const difference = weight - edgeWeight[child];
      edgeWeight[child] = weight;
      add(entry[child], difference); add(leave[child], -difference);
    } else {
      const node = query[1];
      let answer = distance[node];
      for (let index = entry[node] + 1; index > 0; index -= index & -index) answer += changes[index];
      answers.push(answer);
    }
  }
  return answers;
}

const treeQueries = solve;
class Solution {
  treeQueries(n, edges, queries) { return solve(n, edges, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, treeQueries };
