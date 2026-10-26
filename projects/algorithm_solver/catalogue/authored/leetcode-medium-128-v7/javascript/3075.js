'use strict';

// 3075. Maximize Happiness of Selected Children: select descending happiness values and subtract the number of earlier selections.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(happiness, k) {
  const ordered = happiness.slice().sort((left, right) => right - left);
  let total = 0;
  for (let index = 0; index < k; index += 1) {
    const value = ordered[index] - index;
    if (value <= 0) break;
    total += value;
  }
  return total;
}

const maximumHappinessSum = solve;
class Solution {
  maximumHappinessSum(happiness, k) { return solve(happiness, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumHappinessSum };
