'use strict';

// 1849. Splitting a String Into Descending Consecutive Values: try each first value and consume the uniquely determined positive successors.
// O(n^2) digit steps and O(n) bits of integer storage on the at-most-20-digit domain; inputs are read-only.
function solve(s) {
  function matches(start, previous) {
    while (start < s.length) {
      if (previous === 0n) return false;
      const expected = previous - 1n;
      if (expected === 0n) {
        for (let index = start; index < s.length; index += 1) {
          if (s[index] !== '0') return false;
        }
        return true;
      }
      let value = 0n;
      while (start < s.length && value < expected) {
        value = value * 10n + BigInt(s.charCodeAt(start) - 48);
        start += 1;
      }
      if (value !== expected) return false;
      previous = expected;
    }
    return true;
  }
  let first = 0n;
  for (let end = 0; end < s.length - 1; end += 1) {
    first = first * 10n + BigInt(s.charCodeAt(end) - 48);
    if (matches(end + 1, first)) return true;
  }
  return false;
}

const splitString = solve;
class Solution {
  splitString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitString };
