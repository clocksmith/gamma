'use strict';

// 1694. Reformat Phone Number (Easy).
// Specification: https://leetcode.com/problems/reformat-phone-number/description/
// O(n) time and space; format the final four digits as two pairs.
function solve(number) {
  const digits = number.replace(/[ -]/g, '');
  const groups = [];
  let index = 0;
  while (digits.length - index > 4) {
    groups.push(digits.slice(index, index + 3));
    index += 3;
  }
  if (digits.length - index === 4) {
    groups.push(digits.slice(index, index + 2));
    groups.push(digits.slice(index + 2));
  } else {
    groups.push(digits.slice(index));
  }
  return groups.join('-');
}

const reformatNumber = solve;
class Solution {
  reformatNumber(number) { return solve(number); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reformatNumber };
