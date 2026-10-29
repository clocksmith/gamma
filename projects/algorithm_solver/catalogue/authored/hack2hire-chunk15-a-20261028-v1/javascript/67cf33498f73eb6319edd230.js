"use strict";
// Hack2Hire 67cf33498f73eb6319edd230 (Build Longest Palindrome) over an INFERRED spec; qualification unknown.

function solve(words) {
  const count = new Map();
  for (const word of words) count.set(word, (count.get(word) || 0) + 1);
  let pairs = 0, center = 0;
  for (const [word, c] of count) {
    const mirror = word.split("").reverse().join("");
    if (word === mirror) {
      pairs += Math.floor(c / 2);
      if (c % 2) center = 1;
    } else if (word < mirror && count.has(mirror)) {
      pairs += Math.min(c, count.get(mirror));
    }
  }
  return (2 * pairs + center) * words[0].length;
}

function longestPalindrome(words) { return solve(words); }

module.exports = solve;
module.exports.longestPalindrome = longestPalindrome;
