'use strict';

// 1766. Tree of Coprimes.
// Iterative DFS with the nearest active ancestor for each value in [1,50]; O(50*n) time, O(n + 50^2) space. Inputs are preserved.

function solve(nums, edges) {
  const graph = nums.map(() => []);
  for (const [a, b] of edges) { graph[a].push(b); graph[b].push(a); }
  function gcd(a, b) { while (b !== 0) [a, b] = [b, a % b]; return a; }
  const coprime = Array.from({ length: 51 }, (_, value) => {
    const result = [];
    for (let other = 1; other <= 50; other += 1) if (gcd(value, other) === 1) result.push(other);
    return result;
  });
  const nearest = Array.from({ length: 51 }, () => [-1, -1]);
  const answer = Array(nums.length).fill(-1), stack = [[0, -1, 0, null]];
  while (stack.length > 0) {
    const [node, parent, depth, restore] = stack.pop(), value = nums[node];
    if (restore !== null) { nearest[value] = restore; continue; }
    let best = [-1, -1];
    for (const other of coprime[value]) if (nearest[other][1] > best[1]) best = nearest[other];
    answer[node] = best[0];
    const old = nearest[value];
    nearest[value] = [node, depth];
    stack.push([node, parent, depth, old]);
    for (let i = graph[node].length - 1; i >= 0; i -= 1) {
      const neighbor = graph[node][i];
      if (neighbor !== parent) stack.push([neighbor, node, depth + 1, null]);
    }
  }
  return answer;
}

const getCoprimes = solve;
class Solution {
  getCoprimes(nums, edges) { return solve(nums, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getCoprimes };
