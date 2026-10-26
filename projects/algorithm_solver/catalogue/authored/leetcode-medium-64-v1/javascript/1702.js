'use strict';

// 1702. Maximum Binary String After Change: place the sole remaining zero after the leading ones and absorbed zeros.
// O(n) time and O(n) output-construction space; inputs are read-only.
function solve(binary) {
  let zeros = 0;
  for (const bit of binary) if (bit === '0') zeros += 1;
  if (zeros <= 1) return binary;
  const position = binary.indexOf('0') + zeros - 1;
  return '1'.repeat(position) + '0' + '1'.repeat(binary.length - position - 1);
}

const maximumBinaryString = solve;
class Solution {
  maximumBinaryString(binary) { return solve(binary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBinaryString };
