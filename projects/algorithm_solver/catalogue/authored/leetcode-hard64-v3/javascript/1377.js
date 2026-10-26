'use strict';

// 1377. Frog Position After T Seconds: tree traversal with absorbing leaves; O(n) time and O(n) space.

function solve(n, edges, t, target) {
  const neighbors = Array.from({ length: n + 1 }, () => []);
  for (const [first, second] of edges) {
    neighbors[first].push(second);
    neighbors[second].push(first);
  }
  const queue = [[1, 0, 0, 1]];
  for (let head = 0; head < queue.length; head += 1) {
    const [node, parent, elapsed, probability] = queue[head];
    const choices = neighbors[node].length - (parent !== 0 ? 1 : 0);
    if (node === target) return elapsed === t || choices === 0 ? probability : 0;
    if (elapsed === t || choices === 0) continue;
    for (const child of neighbors[node]) {
      if (child !== parent) queue.push([child, node, elapsed + 1, probability / choices]);
    }
  }
  return 0;
}

const frogPosition = solve;
class Solution {
  frogPosition(n, edges, t, target) { return solve(n, edges, t, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, frogPosition };
