'use strict';

// 2045. Second Minimum Time to Reach Destination. Two distinct BFS hop counts, then synchronized-light timing; O(V+E) time and space. Inputs are preserved.

function solve(n, edges, time, change) {
  const neighbors = Array.from({ length: n + 1 }, () => []);
  for (const [first, second] of edges) {
    neighbors[first].push(second);
    neighbors[second].push(first);
  }
  const first = Array(n + 1).fill(Infinity);
  const second = Array(n + 1).fill(Infinity);
  first[1] = 0;
  const queue = [[1, 0]];
  for (let head = 0; head < queue.length; head += 1) {
    const [node, distance] = queue[head];
    if (node === n && distance === second[n]) {
      let elapsed = 0;
      for (let step = 0; step < distance; step += 1) {
        const phase = Math.floor(elapsed / change);
        if (phase % 2 === 1) elapsed = (phase + 1) * change;
        elapsed += time;
      }
      return elapsed;
    }
    const following = distance + 1;
    for (const target of neighbors[node]) {
      if (following < first[target]) {
        first[target] = following;
        queue.push([target, following]);
      } else if (following > first[target] && following < second[target]) {
        second[target] = following;
        queue.push([target, following]);
      }
    }
  }
  return -1;
}

const secondMinimum = solve;
class Solution {
  secondMinimum(n, edges, time, change) { return solve(n, edges, time, change); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, secondMinimum };
