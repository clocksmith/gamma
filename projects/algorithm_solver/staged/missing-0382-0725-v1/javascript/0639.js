'use strict';

// 639. Decode Ways II.

function solve(s) {
  const modulus = 1000000007;
  function single(char) { return char === '*' ? 9 : Number(char !== '0'); }
  function pair(a, b) {
    if (a === '*' && b === '*') return 15;
    if (a === '*') return b <= '6' ? 2 : 1;
    if (b === '*') return a === '1' ? 9 : a === '2' ? 6 : 0;
    const value = Number(a + b); return Number(value >= 10 && value <= 26);
  }
  if (s.length === 0) return 0;
  let previous = 1, current = single(s[0]);
  for (let i = 1; i < s.length; i += 1) [previous, current] = [current, (current * single(s[i]) + previous * pair(s[i - 1], s[i])) % modulus];
  return current;
}

const numDecodings = solve;
class Solution {
  numDecodings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDecodings };
