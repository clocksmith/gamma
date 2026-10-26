'use strict';

// 3751. Total Waviness of Numbers in Range I.
// O((num2 - num1 + 1) log num2) time and O(log num2) auxiliary space; num2 <= 1e5.
function solve(num1, num2) {
  let answer = 0;
  for (let value = num1; value <= num2; value += 1) {
    const digits = String(value);
    for (let index = 1; index + 1 < digits.length; index += 1) {
      if ((digits[index] > digits[index - 1] && digits[index] > digits[index + 1])
        || (digits[index] < digits[index - 1] && digits[index] < digits[index + 1])) answer += 1;
    }
  }
  return answer;
}

const totalWaviness = solve;
class Solution {
  totalWaviness(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalWaviness };
