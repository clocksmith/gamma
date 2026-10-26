'use strict';

// 3715. Sum of Perfect Square Ancestors.
// O(M log log M + n log M) time and O(n + M) space; iterative traversal counts matching square-free kernels.
function solve(n, edges, nums) {
  let maximum = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = Array.from({ length: maximum + 1 }, (_, index) => index);
  for (let prime = 2; prime * prime <= maximum; prime += 1) {
    if (smallest[prime] !== prime) continue;
    for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
      if (smallest[multiple] === multiple) smallest[multiple] = prime;
    }
  }
  const kernels = [];
  for (let value of nums) {
    let kernel = 1;
    while (value > 1) {
      const prime = smallest[value];
      let parity = 0;
      while (value % prime === 0) {
        value /= prime;
        parity ^= 1;
      }
      if (parity !== 0) kernel *= prime;
    }
    kernels.push(kernel);
  }
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const active = new Map();
  let answer = 0;
  const stack = [[0, -1, false]];
  while (stack.length > 0) {
    const [node, parent, leaving] = stack.pop();
    const key = kernels[node];
    if (leaving) {
      active.set(key, active.get(key) - 1);
      continue;
    }
    answer += active.get(key) || 0;
    active.set(key, (active.get(key) || 0) + 1);
    stack.push([node, parent, true]);
    for (const child of graph[node]) {
      if (child !== parent) stack.push([child, node, false]);
    }
  }
  return answer;
}

const sumOfAncestors = solve;
class Solution {
  sumOfAncestors(n, edges, nums) { return solve(n, edges, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfAncestors };
