'use strict';

// O(V + E) time and space. Neither the graph nor its adjacency lists are changed.
function solve(graph) {
  const reverse = Array.from({ length: graph.length }, () => []);
  const remaining = graph.map(neighbors => neighbors.length);
  for (let node = 0; node < graph.length; node += 1) {
    for (const neighbor of graph[node]) reverse[neighbor].push(node);
  }
  const queue = [];
  for (let node = 0; node < graph.length; node += 1) {
    if (remaining[node] === 0) queue.push(node);
  }
  for (let head = 0; head < queue.length; head += 1) {
    for (const predecessor of reverse[queue[head]]) {
      remaining[predecessor] -= 1;
      if (remaining[predecessor] === 0) queue.push(predecessor);
    }
  }
  const result = [];
  for (let node = 0; node < graph.length; node += 1) {
    if (remaining[node] === 0) result.push(node);
  }
  return result;
}

const eventualSafeNodes = solve;
class Solution {
  eventualSafeNodes(graph) { return solve(graph); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, eventualSafeNodes };
