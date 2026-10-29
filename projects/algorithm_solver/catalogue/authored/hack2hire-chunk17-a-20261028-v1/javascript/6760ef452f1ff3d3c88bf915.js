"use strict";
// Hack2Hire 6760ef452f1ff3d3c88bf915 (Smallest Lexicographical Palindrome) over an INFERRED spec; qualification unknown.

function solve(s) {
  const counts = new Array(26).fill(0);
  for (let i = 0; i < s.length; i++) counts[s.charCodeAt(i) - 97]++;
  let half = "", middle = "";
  for (let c = 0; c < 26; c++) {
    const ch = String.fromCharCode(97 + c);
    half += ch.repeat(counts[c] >> 1);
    if (counts[c] % 2) middle += ch;
  }
  return half + middle + half.split("").reverse().join("");
}

function smallestPalindrome(s) { return solve(s); }

module.exports = solve;
module.exports.smallestPalindrome = smallestPalindrome;
