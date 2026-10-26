'use strict';

// 1864. Minimum Number of Swaps to Make the Binary String Alternating: count mismatches against each frequency-feasible alternating pattern.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let zeros = 0;
  let mismatchZero = 0;
  for (let index = 0; index < s.length; index += 1) {
    if (s[index] === '0') zeros += 1;
    if ((s[index] === '1') !== (index % 2 === 1)) mismatchZero += 1;
  }
  const ones = s.length - zeros;
  if (Math.abs(zeros - ones) > 1) return -1;
  const mismatchOne = s.length - mismatchZero;
  if (zeros > ones) return mismatchZero / 2;
  if (ones > zeros) return mismatchOne / 2;
  return Math.min(mismatchZero, mismatchOne) / 2;
}

const minSwaps = solve;
class Solution {
  minSwaps(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
