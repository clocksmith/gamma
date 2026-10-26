'use strict';

// 2867. Count Valid Paths in a Tree. Merge non-prime components and connect their sizes across one prime node; O(n log log(n+2)+n*alpha(n)) time and O(n) space. Inputs are preserved.

function solve(n, edges) {
  const prime = Array(n + 1).fill(true);
  prime[0] = false;
  prime[1] = false;
  for (let factor = 2; factor * factor <= n; factor += 1) {
    if (!prime[factor]) continue;
    for (let multiple = factor * factor; multiple <= n; multiple += factor) prime[multiple] = false;
  }
  const graph = Array.from({ length: n + 1 }, () => []);
  const parent = Array.from({ length: n + 1 }, (_, index) => index);
  const size = Array(n + 1).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
    if (!prime[first] && !prime[second]) {
      let left = find(first);
      let right = find(second);
      if (left === right) continue;
      if (size[left] < size[right]) [left, right] = [right, left];
      parent[right] = left;
      size[left] += size[right];
    }
  }
  let answer = 0;
  for (let node = 2; node <= n; node += 1) {
    if (!prime[node]) continue;
    let seen = 0;
    for (const neighbor of graph[node]) {
      if (prime[neighbor]) continue;
      const count = size[find(neighbor)];
      answer += count * (seen + 1);
      seen += count;
    }
  }
  return answer;
}

const countPaths = solve;
class Solution {
  countPaths(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPaths };
