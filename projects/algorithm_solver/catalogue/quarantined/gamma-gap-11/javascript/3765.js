'use strict';

// 3765. Complete Prime Number.
// O(log(num) * sqrt(num)) time and O(log num) auxiliary space; exact integer divisibility.
function solve(num) {
  function prime(value) {
    if (value < 2) return false;
    if (value % 2 === 0) return value === 2;
    for (let divisor = 3; divisor * divisor <= value; divisor += 2) {
      if (value % divisor === 0) return false;
    }
    return true;
  }
  const digits = String(num);
  for (let length = 1; length <= digits.length; length += 1) {
    if (!prime(Number(digits.slice(0, length))) || !prime(Number(digits.slice(-length)))) return false;
  }
  return true;
}

const completePrime = solve;
class Solution {
  completePrime(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, completePrime };
