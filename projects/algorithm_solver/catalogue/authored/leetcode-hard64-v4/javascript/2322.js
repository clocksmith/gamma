'use strict';

// 2322. Minimum Score After Removals on a Tree. Iterative subtree XORs and ancestor intervals for every cut pair; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums, edges) {
  const size = nums.length;
  const neighbors = Array.from({ length: size }, () => []);
  for (const [first, second] of edges) {
    neighbors[first].push(second);
    neighbors[second].push(first);
  }
  const entering = new Int32Array(size);
  const leaving = new Int32Array(size);
  const subtree = nums.slice();
  let clock = 0;
  const stack = [[0, -1, false]];
  while (stack.length > 0) {
    const [node, parent, exiting] = stack.pop();
    if (exiting) {
      leaving[node] = clock;
      for (const child of neighbors[node]) if (child !== parent) subtree[node] ^= subtree[child];
    } else {
      entering[node] = clock;
      clock += 1;
      stack.push([node, parent, true]);
      for (const child of neighbors[node]) if (child !== parent) stack.push([child, node, false]);
    }
  }
  const total = subtree[0];
  let answer = Infinity;
  for (let first = 1; first < size; first += 1) {
    for (let second = first + 1; second < size; second += 1) {
      let a;
      let b;
      let c;
      if (entering[first] <= entering[second] && entering[second] < leaving[first]) {
        a = subtree[second];
        b = subtree[first] ^ subtree[second];
        c = total ^ subtree[first];
      } else if (entering[second] <= entering[first] && entering[first] < leaving[second]) {
        a = subtree[first];
        b = subtree[second] ^ subtree[first];
        c = total ^ subtree[second];
      } else {
        a = subtree[first];
        b = subtree[second];
        c = total ^ subtree[first] ^ subtree[second];
      }
      answer = Math.min(answer, Math.max(a, b, c) - Math.min(a, b, c));
      if (answer === 0) return 0;
    }
  }
  return answer;
}

const minimumScore = solve;
class Solution {
  minimumScore(nums, edges) { return solve(nums, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumScore };
