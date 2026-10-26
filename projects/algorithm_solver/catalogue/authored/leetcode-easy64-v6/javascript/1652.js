'use strict';

// 1652. Defuse the Bomb (Easy).
// Specification: https://leetcode.com/problems/defuse-the-bomb/description/
// O(n) time, O(1) auxiliary space besides the fresh result; preserve code.
function solve(code, k) {
  const size = code.length;
  const result = new Array(size).fill(0);
  if (k === 0) return result;
  let left = k > 0 ? 1 : size + k;
  let right = k > 0 ? k : size - 1;
  let windowSum = 0;
  for (let index = left; index <= right; index++) windowSum += code[index % size];
  for (let index = 0; index < size; index++) {
    result[index] = windowSum;
    if (index + 1 < size) {
      windowSum -= code[left % size];
      left++;
      right++;
      windowSum += code[right % size];
    }
  }
  return result;
}

const decrypt = solve;
class Solution {
  decrypt(code, k) { return solve(code, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decrypt };
