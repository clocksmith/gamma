'use strict';

// 1276. Number of Burgers with No Waste of Ingredients: solve the two ingredient equations with nonnegative integer counts.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(tomatoSlices, cheeseSlices) {
  const extra = tomatoSlices - 2 * cheeseSlices;
  if (extra < 0 || extra % 2 !== 0 || extra > 2 * cheeseSlices) return [];
  const jumbo = extra / 2;
  return [jumbo, cheeseSlices - jumbo];
}

const numOfBurgers = solve;
class Solution {
  numOfBurgers(tomatoSlices, cheeseSlices) { return solve(tomatoSlices, cheeseSlices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfBurgers };
