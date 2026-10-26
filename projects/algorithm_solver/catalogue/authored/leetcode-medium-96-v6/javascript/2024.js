'use strict';

// 2024. Maximize the Confusion of an Exam: maintain a window whose minority answer count can be changed.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(answerKey, k) {
  let left = 0;
  let trueCount = 0;
  let best = 0;
  for (let right = 0; right < answerKey.length; right += 1) {
    if (answerKey[right] === 'T') trueCount += 1;
    while (Math.min(trueCount, right - left + 1 - trueCount) > k) {
      if (answerKey[left] === 'T') trueCount -= 1;
      left += 1;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

const maxConsecutiveAnswers = solve;
class Solution {
  maxConsecutiveAnswers(answerKey, k) { return solve(answerKey, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxConsecutiveAnswers };
