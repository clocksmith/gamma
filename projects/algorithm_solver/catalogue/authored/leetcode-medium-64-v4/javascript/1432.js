'use strict';

// 1432. Max Difference You Can Get From Changing an Integer: replace the first improvable digit globally while keeping the minimum positive.
// O(d) time and O(d) auxiliary space, where d is the number of digits; inputs are read-only.
function solve(num) {
  const digits = String(num);
  let maximum = digits;
  for (const digit of digits) {
    if (digit !== '9') {
      maximum = digits.split(digit).join('9');
      break;
    }
  }
  let minimum = digits;
  if (digits[0] !== '1') minimum = digits.split(digits[0]).join('1');
  else {
    for (let index = 1; index < digits.length; index += 1) {
      const digit = digits[index];
      if (digit !== '0' && digit !== '1') {
        minimum = digits.split(digit).join('0');
        break;
      }
    }
  }
  return Number(maximum) - Number(minimum);
}

const maxDiff = solve;
class Solution {
  maxDiff(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDiff };
