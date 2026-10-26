'use strict';

// 3849. Maximum Bitwise XOR After Rearrangement.
// O(n) time and O(n) output space; greedily maximize each bit with remaining character counts.
function solve(s, t) {
  const counts = [0, 0];
  for (const char of t) counts[Number(char)] += 1;
  const result = [];
  for (const char of s) {
    const bit = Number(char);
    const opposite = bit ^ 1;
    if (counts[opposite] > 0) {
      counts[opposite] -= 1;
      result.push('1');
    } else {
      counts[bit] -= 1;
      result.push('0');
    }
  }
  return result.join('');
}

const maximumXor = solve;
class Solution {
  maximumXor(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumXor };
