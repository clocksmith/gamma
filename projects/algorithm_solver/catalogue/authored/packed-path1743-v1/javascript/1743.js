'use strict';

// Linked memory repair of the owner-provided 1743 implementation, not an edit.
// Official domain: a simple path on unique integers in [-100000,100000].
// One Map stores degree and XOR of neighbors as an exactly represented Number.
// Degree 1: unsigned neighbor. Degree 2: 2^32 + unsigned XOR of both neighbors.
// O(n) expected time and O(n) space, with no per-vertex neighbor arrays.
// The caller's adjacentPairs and all rows are read-only; output is fresh.
function solve(adjacentPairs) {
  const degreeTwo = 4294967296;
  const graph = new Map();
  function add(node, neighbor) {
    const old = graph.get(node);
    if (old === undefined) graph.set(node, neighbor >>> 0);
    else graph.set(node, degreeTwo + ((old ^ neighbor) >>> 0));
  }
  for (const [left, right] of adjacentPairs) {
    add(left, right);
    add(right, left);
  }
  let start = Infinity;
  for (const [node, packed] of graph) {
    if (packed < degreeTwo && node < start) start = node;
  }
  const size = graph.size;
  const answer = new Array(size);
  answer[0] = start;
  let current = start;
  let previous = 0; // Unused at the initial endpoint, including when its neighbor is 0.
  for (let index = 1; index < size; index += 1) {
    const packed = graph.get(current);
    const next = packed < degreeTwo ? (packed | 0) : ((packed - degreeTwo) ^ previous);
    graph.delete(current); // Release visited local entries before return/transport.
    answer[index] = next;
    previous = current;
    current = next;
  }
  return answer;
}

const restoreArray = solve;
class Solution {
  restoreArray(adjacentPairs) { return solve(adjacentPairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, restoreArray };
