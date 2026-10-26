'use strict';

// 2929. Distribute Candies Among Children II: exclude children exceeding their limit from the unconstrained three-way compositions.
// O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n, limit) {
  function unrestricted(total) {
    return total >= 0 ? (total + 1) * (total + 2) / 2 : 0;
  }
  const step = limit + 1;
  return unrestricted(n) - 3 * unrestricted(n - step)
    + 3 * unrestricted(n - 2 * step) - unrestricted(n - 3 * step);
}

const distributeCandies = solve;
class Solution {
  distributeCandies(n, limit) { return solve(n, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distributeCandies };
