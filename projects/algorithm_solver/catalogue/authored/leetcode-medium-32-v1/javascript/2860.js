'use strict';

// 2860. Happy Students: count valid selection sizes between sorted thresholds.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const values = [...nums].sort((left, right) => left - right);
  let answer = values[0] > 0 ? 1 : 0;
  for (let selected = 1; selected <= values.length; selected += 1) {
    if (values[selected - 1] < selected
        && (selected === values.length || values[selected] > selected)) {
      answer += 1;
    }
  }
  return answer;
}

const countWays = solve;
class Solution {
  countWays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countWays };
