'use strict';

// 3871. Count Commas in Range II.
// O(log_1000(n)) time and O(1) space; count one extra comma at each thousand-power threshold.
function solve(n) {
  let answer = 0;
  let threshold = 1000;
  while (threshold <= n) {
    answer += n - threshold + 1;
    if (threshold > Math.floor(n / 1000)) break;
    threshold *= 1000;
  }
  return answer;
}

const countCommas = solve;
class Solution {
  countCommas(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCommas };
