'use strict';

// 3606. Coupon Code Validator (Easy).
// Specification: https://leetcode.com/problems/coupon-code-validator/description/
// O(n * L * log(n + 1)) time, O(n) reference space; ASCII ordering; preserve inputs.
function solve(code, businessLine, isActive) {
  const categories = ['electronics', 'grocery', 'pharmacy', 'restaurant'];
  const groups = categories.map(() => []);
  for (let index = 0; index < code.length; index++) {
    const category = categories.indexOf(businessLine[index]);
    if (!isActive[index] || category < 0 || code[index].length === 0) continue;
    let valid = true;
    for (const character of code[index]) {
      if (!(character >= 'a' && character <= 'z') &&
          !(character >= 'A' && character <= 'Z') &&
          !(character >= '0' && character <= '9') && character !== '_') {
        valid = false;
        break;
      }
    }
    if (valid) groups[category].push(code[index]);
  }
  const result = [];
  for (const group of groups) {
    group.sort();
    for (const value of group) result.push(value);
  }
  return result;
}

const validateCoupons = solve;
class Solution {
  validateCoupons(code, businessLine, isActive) { return solve(code, businessLine, isActive); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validateCoupons };
