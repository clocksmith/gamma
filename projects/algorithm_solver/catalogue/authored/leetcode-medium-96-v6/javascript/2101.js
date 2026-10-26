'use strict';

// 2101. Detonate the Maximum Bombs: build directed radius reachability and explore every possible first detonation.
// O(n^3) time and O(n^2) auxiliary space; inputs are read-only.
function solve(bombs) {
  const size = bombs.length;
  const graph = Array.from({ length: size }, () => []);
  for (let left = 0; left < size; left += 1) {
    const [x, y, radius] = bombs[left];
    for (let right = 0; right < size; right += 1) {
      const dx = x - bombs[right][0];
      const dy = y - bombs[right][1];
      if (left !== right && dx * dx + dy * dy <= radius * radius) graph[left].push(right);
    }
  }
  let best = 0;
  for (let start = 0; start < size; start += 1) {
    const seen = new Set([start]);
    const stack = [start];
    while (stack.length) {
      for (const neighbor of graph[stack.pop()]) {
        if (!seen.has(neighbor)) {
          seen.add(neighbor);
          stack.push(neighbor);
        }
      }
    }
    best = Math.max(best, seen.size);
    if (best === size) break;
  }
  return best;
}

const maximumDetonation = solve;
class Solution {
  maximumDetonation(bombs) { return solve(bombs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumDetonation };
