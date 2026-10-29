"use strict";
// Hack2Hire 67883eb4e20f8f324213c2a2 (Next Greater Palindrome) over an INFERRED spec; qualification unknown.

function solve(n) {
  const length = n.length;
  const mirrorOf = (half) => half + half.slice(0, length >> 1).split("").reverse().join("");
  let allNines = true;
  for (let i = 0; i < length; i++) if (n[i] !== "9") { allNines = false; break; }
  if (allNines) return "1" + "0".repeat(length - 1) + "1";
  let half = n.slice(0, (length + 1) >> 1);
  const mirror = mirrorOf(half);
  if (mirror > n) return mirror;
  const digits = half.split("");
  let i = digits.length - 1;
  while (digits[i] === "9") { digits[i] = "0"; i--; }
  digits[i] = String.fromCharCode(digits[i].charCodeAt(0) + 1);
  half = digits.join("");
  return mirrorOf(half);
}

function nextGreaterPalindrome(n) { return solve(n); }

module.exports = solve;
module.exports.nextGreaterPalindrome = nextGreaterPalindrome;
