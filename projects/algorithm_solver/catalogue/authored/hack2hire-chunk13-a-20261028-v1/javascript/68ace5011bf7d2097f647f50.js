"use strict";
// Hack2Hire 68ace5011bf7d2097f647f50 (Palindrome Check with Ignore Set) over an INFERRED spec; qualification unknown.

function solve(ignoreArray, inputArray) {
  const ignore = new Set(ignoreArray);
  let left = 0, right = inputArray.length - 1;
  while (left < right) {
    if (ignore.has(inputArray[left])) left++;
    else if (ignore.has(inputArray[right])) right--;
    else if (inputArray[left] !== inputArray[right]) return false;
    else { left++; right--; }
  }
  return true;
}

function isPalindromeIgnoring(ignoreArray, inputArray) { return solve(ignoreArray, inputArray); }

module.exports = solve;
module.exports.isPalindromeIgnoring = isPalindromeIgnoring;
