'use strict';

// 1788. Maximize the Beauty of the Garden.
// O(n) expected time and space. All sums fit exactly within Number for the input bounds.
function solve(flowers) {
  let prefix = 0;
  const afterFirst = new Map();
  let minimum = flowers[0];
  for (const value of flowers) minimum = Math.min(minimum, value);
  let answer = 2 * minimum;
  for (const value of flowers) {
    if (afterFirst.has(value)) answer = Math.max(answer, 2 * value + prefix - afterFirst.get(value));
    prefix += Math.max(value, 0);
    if (!afterFirst.has(value)) afterFirst.set(value, prefix);
  }
  return answer;
}

const maximumBeauty = solve;
class Solution {
  maximumBeauty(flowers) { return solve(flowers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBeauty };
