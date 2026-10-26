'use strict';

// 2359. Find Closest Node to Given Two Nodes: record both functional-graph distances and minimize the larger one.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(edges, node1, node2) {
  function distances(start) {
    const result = new Int32Array(edges.length).fill(-1);
    let node = start;
    let distance = 0;
    while (node !== -1 && result[node] === -1) {
      result[node] = distance;
      distance += 1;
      node = edges[node];
    }
    return result;
  }
  const first = distances(node1);
  const second = distances(node2);
  let answer = -1;
  let best = edges.length + 1;
  for (let node = 0; node < edges.length; node += 1) {
    if (first[node] >= 0 && second[node] >= 0) {
      const cost = Math.max(first[node], second[node]);
      if (cost < best) {
        answer = node;
        best = cost;
      }
    }
  }
  return answer;
}

const closestMeetingNode = solve;
class Solution {
  closestMeetingNode(edges, node1, node2) { return solve(edges, node1, node2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestMeetingNode };
