'use strict';

// 443. String Compression. Required in-place prefix rewrite; returns its length and leaves the suffix unspecified.

function solve(chars) {
  let read = 0, write = 0;
  while (read < chars.length) {
    let end = read + 1;
    while (end < chars.length && chars[end] === chars[read]) end += 1;
    chars[write++] = chars[read];
    if (end - read > 1) for (const digit of String(end - read)) chars[write++] = digit;
    read = end;
  }
  return write;
}

const compress = solve;
class Solution {
  compress(chars) { return solve(chars); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, compress };
