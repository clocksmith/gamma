'use strict';

// 1782. Count Pairs Of Nodes. Sorted degrees with parallel-edge corrections; O(n log n + E + Q*(n+E)) time, O(n+E) space. Inputs are preserved.

function solve(n, edges, queries) {
  const degree = Array(n).fill(0);
  const shared = new Map();
  for (const [first, second] of edges) {
    const left = Math.min(first, second) - 1;
    const right = Math.max(first, second) - 1;
    degree[left] += 1;
    degree[right] += 1;
    const key = left * n + right;
    shared.set(key, (shared.get(key) || 0) + 1);
  }
  const ordered = degree.slice().sort((a, b) => a - b);
  const answer = [];
  for (const threshold of queries) {
    let left = 0;
    let right = n - 1;
    let count = 0;
    while (left < right) {
      if (ordered[left] + ordered[right] > threshold) {
        count += right - left;
        right -= 1;
      } else {
        left += 1;
      }
    }
    for (const [key, overlap] of shared) {
      const first = Math.floor(key / n);
      const second = key % n;
      const total = degree[first] + degree[second];
      if (total > threshold && total - overlap <= threshold) count -= 1;
    }
    answer.push(count);
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(n, edges, queries) { return solve(n, edges, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
