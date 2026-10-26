'use strict';

// 2683. Neighboring Bitwise XOR: require the cyclic xor differences to cancel.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(derived) {
  let parity = 0;
  for (const value of derived) parity ^= value;
  return parity === 0;
}

const doesValidArrayExist = solve;
class Solution {
  doesValidArrayExist(derived) { return solve(derived); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, doesValidArrayExist };
