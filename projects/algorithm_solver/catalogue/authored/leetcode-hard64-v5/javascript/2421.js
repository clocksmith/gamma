'use strict';

// 2421. Number of Good Paths. Activate equal-value groups and count endpoints within union-find components; O(n log n) time and O(n) space for a tree. Inputs are preserved.

function solve(vals, edges) {
  const size = vals.length;
  const graph = Array.from({ length: size }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = Array.from({ length: size }, (_, index) => index);
  const weight = Array(size).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  function merge(first, second) {
    first = find(first);
    second = find(second);
    if (first === second) return;
    if (weight[first] < weight[second]) [first, second] = [second, first];
    parent[second] = first;
    weight[first] += weight[second];
  }
  const order = Array.from({ length: size }, (_, index) => index).sort((a, b) => vals[a] - vals[b]);
  let answer = 0;
  let begin = 0;
  while (begin < size) {
    let end = begin;
    const value = vals[order[begin]];
    while (end < size && vals[order[end]] === value) {
      for (const neighbor of graph[order[end]]) if (vals[neighbor] <= value) merge(order[end], neighbor);
      end += 1;
    }
    const counts = new Map();
    for (let index = begin; index < end; index += 1) {
      const root = find(order[index]);
      counts.set(root, (counts.get(root) || 0) + 1);
    }
    for (const count of counts.values()) answer += count * (count + 1) / 2;
    begin = end;
  }
  return answer;
}

const numberOfGoodPaths = solve;
class Solution {
  numberOfGoodPaths(vals, edges) { return solve(vals, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfGoodPaths };
