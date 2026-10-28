'use strict';

// 443. String Compression (Medium).
// Specification: https://leetcode.com/problems/string-compression/description/
function solve(chars) {
  const result = [];
  let i = 0;
  while (i < chars.length) {
    const ch = chars[i];
    let count = 0;
    while (i < chars.length && chars[i] === ch) { i++; count++; }
    result.push(ch);
    if (count > 1) { for (const digit of String(count)) result.push(digit); }
  }
  return result;
}
const compress = solve;
class Solution { compress(chars) { return solve(chars); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, compress };
