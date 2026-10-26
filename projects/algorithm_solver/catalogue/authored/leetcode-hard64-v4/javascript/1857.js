'use strict';

// 1857. Largest Color Value in a Directed Graph. Topological color-count DP and explicit cycle detection; O(26*(V+E)) time and O(26*V+E) space. Inputs are preserved.

function solve(colors, edges) {
  const size = colors.length;
  const neighbors = Array.from({ length: size }, () => []);
  const incoming = new Int32Array(size);
  for (const [source, target] of edges) {
    neighbors[source].push(target);
    incoming[target] += 1;
  }
  const queue = [];
  for (let node = 0; node < size; node += 1) if (incoming[node] === 0) queue.push(node);
  const counts = new Int32Array(size * 26);
  let answer = 0;
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    const offset = node * 26;
    counts[offset + colors.charCodeAt(node) - 97] += 1;
    for (let color = 0; color < 26; color += 1) answer = Math.max(answer, counts[offset + color]);
    for (const target of neighbors[node]) {
      const nextOffset = target * 26;
      for (let color = 0; color < 26; color += 1) {
        counts[nextOffset + color] = Math.max(counts[nextOffset + color], counts[offset + color]);
      }
      incoming[target] -= 1;
      if (incoming[target] === 0) queue.push(target);
    }
  }
  return queue.length === size ? answer : -1;
}

const largestPathValue = solve;
class Solution {
  largestPathValue(colors, edges) { return solve(colors, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestPathValue };
