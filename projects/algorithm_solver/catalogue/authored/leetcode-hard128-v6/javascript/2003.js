'use strict';

// 2003. Smallest Missing Genetic Value in Each Subtree.
// Only ancestors of value 1 can differ from 1; visit each newly exposed subtree once. O(n) expected time and space. Inputs are preserved.

function solve(parents, nums) {
  const answer = Array(nums.length).fill(1);
  let node = nums.indexOf(1);
  if (node === -1) return answer;
  const children = nums.map(() => []);
  parents.forEach((parent, child) => { if (parent !== -1) children[parent].push(child); });
  const visited = new Uint8Array(nums.length), values = new Set();
  let missing = 1;
  while (node !== -1) {
    const stack = [node];
    while (stack.length > 0) {
      const current = stack.pop();
      if (visited[current]) continue;
      visited[current] = 1; values.add(nums[current]);
      for (const child of children[current]) stack.push(child);
    }
    while (values.has(missing)) missing += 1;
    answer[node] = missing; node = parents[node];
  }
  return answer;
}

const smallestMissingValueSubtree = solve;
class Solution {
  smallestMissingValueSubtree(parents, nums) { return solve(parents, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestMissingValueSubtree };
