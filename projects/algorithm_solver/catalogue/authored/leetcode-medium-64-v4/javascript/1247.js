'use strict';

// 1247. Minimum Swaps to Make Strings Equal: pair opposite mismatch types and handle the remaining pair.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s1, s2) {
  let xy = 0;
  let yx = 0;
  for (let index = 0; index < s1.length; index += 1) {
    if (s1[index] === s2[index]) continue;
    if (s1[index] === 'x') xy += 1;
    else yx += 1;
  }
  if ((xy + yx) % 2 !== 0) return -1;
  return Math.floor(xy / 2) + Math.floor(yx / 2) + 2 * (xy % 2);
}

const minimumSwap = solve;
class Solution {
  minimumSwap(s1, s2) { return solve(s1, s2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSwap };
