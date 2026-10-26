'use strict';

// 2872. Maximum Number of K-Divisible Components. Close every divisible subtree while accumulating remainders in iterative postorder; O(n) time and O(n) space. Inputs are preserved.

function solve(n, edges, values, k) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      order.push(neighbor);
    }
  }
  const remainder = values.map(value => value % k);
  let answer = 0;
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    if (remainder[node] === 0) {
      answer += 1;
    } else if (parent[node] !== -1) {
      const previous = parent[node];
      remainder[previous] = (remainder[previous] + remainder[node]) % k;
    }
  }
  return answer;
}

const maxKDivisibleComponents = solve;
class Solution {
  maxKDivisibleComponents(n, edges, values, k) { return solve(n, edges, values, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxKDivisibleComponents };
