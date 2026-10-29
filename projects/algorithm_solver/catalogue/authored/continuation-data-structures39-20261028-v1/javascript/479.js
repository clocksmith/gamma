"use strict";

function solve(n) {
  if (n === 1) return 9;
  const upper = BigInt(10 ** n - 1);
  const lower = BigInt(10 ** (n - 1));
  for (let left = Number(upper); left >= Number(lower); left--) {
    const s = String(left);
    let rev = "";
    for (let i = s.length - 1; i >= 0; i--) rev += s[i];
    const pal = BigInt(s + rev);
    for (let d = upper; d * d >= pal; d--) {
      if (pal % d === 0n) {
        const q = pal / d;
        if (q >= lower && q <= upper) {
          return Number(pal % 1337n);
        }
      }
    }
  }
  return 9;
}

function largestPalindrome(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.largestPalindrome = largestPalindrome;
