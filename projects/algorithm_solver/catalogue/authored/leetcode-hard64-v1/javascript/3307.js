'use strict';

// 3307. Find the K-th Character in String Game II: read the doubling ancestry from the bits of k minus one.
// O(log k) time and O(1) auxiliary space. Inputs are preserved.
function solve(k, operations) {
  // BigInt keeps position shifts exact beyond JavaScript's 32-bit bitwise domain.
  let position = BigInt(k) - 1n;
  let shift = 0;
  let index = 0;
  while (position > 0n) {
    if (position & 1n) shift = (shift + operations[index]) % 26;
    position >>= 1n;
    index += 1;
  }
  return String.fromCharCode(97 + shift);
}

const kthCharacter = solve;
class Solution {
  kthCharacter(k, operations) { return solve(k, operations); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthCharacter };
