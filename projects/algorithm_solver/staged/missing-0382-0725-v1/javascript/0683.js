'use strict';

// 683. K Empty Slots. Linear scan of activation-day windows; interior bulbs must all activate later.

function solve(bulbs, k) {
  const n = bulbs.length, days = Array(n).fill(0);
  bulbs.forEach((position, day) => { days[position - 1] = day + 1; });
  let left = 0, right = k + 1, index = 1, answer = n + 1;
  while (right < n) {
    if (index === right) {
      answer = Math.min(answer, Math.max(days[left], days[right]));
      left = right; right = left + k + 1; index = left + 1;
    } else if (days[index] < days[left] || days[index] < days[right]) {
      left = index; right = left + k + 1; index = left + 1;
    } else index += 1;
  }
  return answer <= n ? answer : -1;
}

const kEmptySlots = solve;
class Solution {
  kEmptySlots(bulbs, k) { return solve(bulbs, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kEmptySlots };
