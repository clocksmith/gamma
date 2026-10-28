'use strict';

// 1053. Previous Permutation With One Swap (Medium).
// Specification: https://leetcode.com/problems/previous-permutation-with-one-swap/description/
function solve(arr) {
  const result = arr.slice();
  let index = -1;
  for (let i = result.length - 2; i >= 0; i--) { if (result[i] > result[i + 1]) { index = i; break; } }
  if (index === -1) return result;
  let bestValue = -Infinity; let bestIndex = -1;
  for (let j = index + 1; j < result.length; j++) {
    if (result[j] < result[index] && result[j] > bestValue) { bestValue = result[j]; bestIndex = j; }
  }
  const tmp = result[index]; result[index] = result[bestIndex]; result[bestIndex] = tmp;
  return result;
}
const prevPermOpt1 = solve;
class Solution { prevPermOpt1(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, prevPermOpt1 };
