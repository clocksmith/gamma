'use strict';

// 444. Sequence Reconstruction. Require a unique topological choice matching nums at every step.

function solve(nums, sequences) {
  const n = nums.length, graph = Array.from({length: n + 1}, () => new Set());
  const indegree = Array(n + 1).fill(0), seen = new Set();
  for (const sequence of sequences) {
    for (const value of sequence) { if (value < 1 || value > n) return false; seen.add(value); }
    for (let i = 1; i < sequence.length; i += 1) {
      const a = sequence[i - 1], b = sequence[i];
      if (!graph[a].has(b)) { graph[a].add(b); indegree[b] += 1; }
    }
  }
  if (seen.size !== n) return false;
  const queue = [];
  for (let i = 1; i <= n; i += 1) if (indegree[i] === 0) queue.push(i);
  let head = 0, index = 0;
  while (head < queue.length) {
    if (queue.length - head !== 1) return false;
    const value = queue[head++];
    if (index >= n || nums[index++] !== value) return false;
    for (const neighbor of graph[value]) {
      indegree[neighbor] -= 1;
      if (indegree[neighbor] === 0) queue.push(neighbor);
    }
  }
  return index === n;
}

const sequenceReconstruction = solve;
class Solution {
  sequenceReconstruction(nums, sequences) { return solve(nums, sequences); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sequenceReconstruction };
