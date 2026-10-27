'use strict';

// 421. Maximum XOR of Two Numbers in an Array. Build the answer from high bits using complementary prefixes.

function solve(nums) {
  let answer = 0, mask = 0;
  for (let bit = 30; bit >= 0; bit -= 1) {
    mask |= 1 << bit;
    const prefixes = new Set(nums.map(value => value & mask));
    const candidate = answer | (1 << bit);
    for (const prefix of prefixes) {
      if (prefixes.has(candidate ^ prefix)) { answer = candidate; break; }
    }
  }
  return answer;
}

const findMaximumXOR = solve;
class Solution {
  findMaximumXOR(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximumXOR };
