'use strict';

// 1720. Decode XORed Array (Easy).
// Specification: https://leetcode.com/problems/decode-xored-array/description/
function solve(encoded, first) {
  const result = [first];
  for (const value of encoded) result.push(result[result.length - 1] ^ value);
  return result;
}
const decode = solve;
class Solution { decode(encoded, first) { return solve(encoded, first); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, decode };
