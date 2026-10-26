'use strict';

// 2097. Valid Arrangement of Pairs. Iterative Hierholzer traversal of the guaranteed Euler trail; O(E) time and space. Inputs are preserved.

function solve(pairs) {
  const neighbors = new Map();
  const balance = new Map();
  for (const [first, second] of pairs) {
    if (!neighbors.has(first)) neighbors.set(first, []);
    neighbors.get(first).push(second);
    balance.set(first, (balance.get(first) || 0) + 1);
    balance.set(second, (balance.get(second) || 0) - 1);
  }
  let start = pairs[0][0];
  for (const [node, difference] of balance) {
    if (difference === 1) {
      start = node;
      break;
    }
  }
  const stack = [start];
  const path = [];
  while (stack.length > 0) {
    const node = stack[stack.length - 1];
    const next = neighbors.get(node);
    if (next && next.length > 0) stack.push(next.pop());
    else path.push(stack.pop());
  }
  path.reverse();
  const answer = [];
  for (let index = 0; index + 1 < path.length; index += 1) answer.push([path[index], path[index + 1]]);
  return answer;
}

const validArrangement = solve;
class Solution {
  validArrangement(pairs) { return solve(pairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validArrangement };
