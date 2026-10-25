'use strict';

// 928. Minimize Malware Spread II.
// O(n^2) time, O(n) space. Initially infected nodes are excluded from components.
function solve(graph, initial) {
  const size = graph.length;
  const infected = new Uint8Array(size);
  for (const node of initial) infected[node] = 1;
  const visited = new Uint8Array(size);
  const saved = new Int32Array(size);
  for (let start = 0; start < size; start += 1) {
    if (infected[start] || visited[start]) continue;
    const stack = [start];
    visited[start] = 1;
    let count = 0;
    const sources = new Set();
    while (stack.length > 0) {
      const node = stack.pop();
      count += 1;
      for (let neighbor = 0; neighbor < size; neighbor += 1) {
        if (!graph[node][neighbor]) continue;
        if (infected[neighbor]) {
          sources.add(neighbor);
        } else if (!visited[neighbor]) {
          visited[neighbor] = 1;
          stack.push(neighbor);
        }
      }
    }
    if (sources.size === 1) saved[sources.values().next().value] += count;
  }
  let answer = initial[0];
  for (const node of initial) {
    if (saved[node] > saved[answer] || (saved[node] === saved[answer] && node < answer)) {
      answer = node;
    }
  }
  return answer;
}

const minMalwareSpread = solve;
class Solution {
  minMalwareSpread(graph, initial) { return solve(graph, initial); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMalwareSpread };
