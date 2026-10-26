'use strict';

// 1938. Maximum Genetic Difference Query.
// Maintain a counted binary trie along an iterative ancestor traversal; O((n+q)*B) time and space. Inputs are preserved.

function solve(parents, queries) {
  const n = parents.length, children = parents.map(() => []), attached = parents.map(() => []);
  let root = 0, maximum = n - 1;
  parents.forEach((parent, node) => { if (parent === -1) root = node; else children[parent].push(node); });
  queries.forEach(([node, value], index) => { attached[node].push([value, index]); maximum = Math.max(maximum, value); });
  const bits = Math.max(1, Math.floor(Math.log2(Math.max(1, maximum))) + 1);
  const branch = [[-1, -1]], count = [0];
  function update(value, change) {
    let state = 0;
    count[state] += change;
    for (let bit = bits - 1; bit >= 0; bit -= 1) {
      const digit = (value >>> bit) & 1;
      if (branch[state][digit] === -1) { branch[state][digit] = branch.length; branch.push([-1, -1]); count.push(0); }
      state = branch[state][digit]; count[state] += change;
    }
  }
  const answer = Array(queries.length).fill(0), stack = [[root, false]];
  while (stack.length > 0) {
    const [node, leaving] = stack.pop();
    if (leaving) { update(node, -1); continue; }
    update(node, 1);
    for (const [value, index] of attached[node]) {
      let state = 0, score = 0;
      for (let bit = bits - 1; bit >= 0; bit -= 1) {
        const digit = (value >>> bit) & 1, opposite = branch[state][digit ^ 1];
        if (opposite !== -1 && count[opposite] > 0) { score += 2 ** bit; state = opposite; }
        else state = branch[state][digit];
      }
      answer[index] = score;
    }
    stack.push([node, true]);
    for (let i = children[node].length - 1; i >= 0; i -= 1) stack.push([children[node][i], false]);
  }
  return answer;
}

const maxGeneticDifference = solve;
class Solution {
  maxGeneticDifference(parents, queries) { return solve(parents, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxGeneticDifference };
