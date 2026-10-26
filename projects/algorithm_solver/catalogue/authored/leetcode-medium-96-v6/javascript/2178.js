'use strict';

// 2178. Maximum Split of Positive Even Integers: take the smallest unused even values and add the final remainder to the largest.
// O(sqrt(S)) time and result space for S = finalSum; inputs are read-only.
function solve(finalSum) {
  if (finalSum % 2) return [];
  let remaining = finalSum;
  const result = [];
  let value = 2;
  while (remaining >= value) {
    result.push(value);
    remaining -= value;
    value += 2;
  }
  if (remaining) result[result.length - 1] += remaining;
  return result;
}

const maximumEvenSplit = solve;
class Solution {
  maximumEvenSplit(finalSum) { return solve(finalSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumEvenSplit };
