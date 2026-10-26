'use strict';

// 2469. Convert the Temperature (Easy).
// Specification: https://leetcode.com/problems/convert-the-temperature/description/
// O(1) time and space; return Kelvin then Fahrenheit using the specified binary64 arithmetic.
function solve(celsius) {
  return [celsius + 273.15, celsius * 1.8 + 32.0];
}

const convertTemperature = solve;
class Solution {
  convertTemperature(celsius) { return solve(celsius); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, convertTemperature };
