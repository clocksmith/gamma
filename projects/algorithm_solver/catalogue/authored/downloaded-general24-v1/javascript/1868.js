'use strict';

// 1868. Product of Two Run-Length Encoded Arrays (Medium).
// Specification: https://leetcode.com/problems/product-of-two-run-length-encoded-arrays/description/
function solve(encoded1, encoded2) {
  let i = 0; let j = 0;
  let remaining1 = encoded1.length > 0 ? encoded1[0][1] : 0;
  let remaining2 = encoded2.length > 0 ? encoded2[0][1] : 0;
  const result = [];
  while (i < encoded1.length && j < encoded2.length) {
    const count = Math.min(remaining1, remaining2);
    const product = encoded1[i][0] * encoded2[j][0];
    if (result.length > 0 && result[result.length - 1][0] === product) result[result.length - 1][1] += count;
    else result.push([product, count]);
    remaining1 -= count; remaining2 -= count;
    if (remaining1 === 0) { i++; if (i < encoded1.length) remaining1 = encoded1[i][1]; }
    if (remaining2 === 0) { j++; if (j < encoded2.length) remaining2 = encoded2[j][1]; }
  }
  return result;
}
const findRLEArray = solve;
class Solution { findRLEArray(encoded1, encoded2) { return solve(encoded1, encoded2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRLEArray };
