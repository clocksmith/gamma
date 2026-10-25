'use strict';

// O(n) time/space. Iterative leaf removal supports arbitrary valid vertex labels.
function solve(parent, s) {
  const size = parent.length;
  const remaining = Array(size).fill(0);
  for (let node = 1; node < size; node += 1) remaining[parent[node]] += 1;
  const first = Array(size).fill(0);
  const second = Array(size).fill(0);
  const queue = [];
  for (let node = 0; node < size; node += 1) {
    if (remaining[node] === 0) queue.push(node);
  }
  let best = 1;
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    best = Math.max(best, 1 + first[node] + second[node]);
    const ancestor = parent[node];
    if (ancestor === -1) continue;
    if (s[node] !== s[ancestor]) {
      const length = first[node] + 1;
      if (length > first[ancestor]) {
        second[ancestor] = first[ancestor];
        first[ancestor] = length;
      } else if (length > second[ancestor]) second[ancestor] = length;
    }
    remaining[ancestor] -= 1;
    if (remaining[ancestor] === 0) queue.push(ancestor);
  }
  return best;
}

const longestPath = solve;
class Solution {
  longestPath(parent, s) { return solve(parent, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPath };
