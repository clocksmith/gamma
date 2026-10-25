'use strict';

// 1743. Restore the Array From Adjacent Pairs: walk the path from its smaller endpoint.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(adjacentPairs) {
  const graph = new Map();
  for (const [left, right] of adjacentPairs) {
    if (!graph.has(left)) graph.set(left, []);
    if (!graph.has(right)) graph.set(right, []);
    graph.get(left).push(right);
    graph.get(right).push(left);
  }
  let start = Infinity;
  for (const [value, neighbors] of graph) {
    if (neighbors.length === 1) start = Math.min(start, value);
  }
  const answer = [start];
  let previous = null;
  let current = start;
  while (answer.length < graph.size) {
    for (const neighbor of graph.get(current)) {
      if (neighbor !== previous) {
        answer.push(neighbor);
        previous = current;
        current = neighbor;
        break;
      }
    }
  }
  return answer;
}

const restoreArray = solve;
class Solution {
  restoreArray(adjacentPairs) { return solve(adjacentPairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, restoreArray };
