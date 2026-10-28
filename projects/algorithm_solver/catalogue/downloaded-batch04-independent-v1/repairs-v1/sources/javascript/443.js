'use strict';

// 443. String Compression (Medium).
// Specification: https://leetcode.com/problems/string-compression/description/
function* countDigits(count) {
  let divisor = 1;
  while (divisor * 10 <= count) divisor *= 10;
  while (divisor > 0) {
    yield String.fromCharCode(48 + Math.floor(count / divisor));
    count %= divisor;
    divisor = Math.floor(divisor / 10);
  }
}
function compressInPlace(chars) {
  let read = 0, write = 0;
  while (read < chars.length) {
    const first = read, value = chars[read];
    while (read < chars.length && chars[read] === value) read++;
    chars[write++] = value;
    if (read - first > 1) for (const digit of countDigits(read - first)) chars[write++] = digit;
  }
  return write;
}
function solve(chars) {
  const result = [];
  let read = 0;
  while (read < chars.length) {
    const first = read, value = chars[read];
    while (read < chars.length && chars[read] === value) read++;
    result.push(value);
    if (read - first > 1) for (const digit of countDigits(read - first)) result.push(digit);
  }
  return result;
}
const compress = solve;
class Solution { compress(chars) { return compressInPlace(chars); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, compress };
