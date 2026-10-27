'use strict';
// 133. Clone Graph.
class Node {
  constructor(val = 0, neighbors = []) { this.val = val; this.neighbors = neighbors; }
}
function solve(node) {
  if (node === null) return null;
  const copies = new Map([[node, new Node(node.val)]]);
  const queue = [node];
  for (let head = 0; head < queue.length; head += 1) {
    const current = queue[head];
    for (const neighbor of current.neighbors) {
      if (!copies.has(neighbor)) { copies.set(neighbor, new Node(neighbor.val)); queue.push(neighbor); }
      copies.get(current).neighbors.push(copies.get(neighbor));
    }
  }
  return copies.get(node);
}
const cloneGraph = solve;
class Solution { cloneGraph(node) { return solve(node); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, cloneGraph, Node };
