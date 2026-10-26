'use strict';

// 2866. Beautiful Towers II: combine capped prefix and suffix sums obtained from monotone stacks.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(maxHeights) {
  const size = maxHeights.length;
  const prefix = new Array(size).fill(0);
  const stack = [];
  for (let index = 0; index < size; index += 1) {
    const height = maxHeights[index];
    while (stack.length && maxHeights[stack[stack.length - 1]] > height) stack.pop();
    const previous = stack.length ? stack[stack.length - 1] : -1;
    prefix[index] = height * (index - previous) + (previous >= 0 ? prefix[previous] : 0);
    stack.push(index);
  }
  const suffix = new Array(size).fill(0);
  stack.length = 0;
  let best = 0;
  for (let index = size - 1; index >= 0; index -= 1) {
    const height = maxHeights[index];
    while (stack.length && maxHeights[stack[stack.length - 1]] > height) stack.pop();
    const following = stack.length ? stack[stack.length - 1] : size;
    suffix[index] = height * (following - index) + (following < size ? suffix[following] : 0);
    best = Math.max(best, prefix[index] + suffix[index] - height);
    stack.push(index);
  }
  return best;
}

const maximumSumOfHeights = solve;
class Solution {
  maximumSumOfHeights(maxHeights) { return solve(maxHeights); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSumOfHeights };
