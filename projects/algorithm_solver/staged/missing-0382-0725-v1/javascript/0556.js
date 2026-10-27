'use strict';

// 556. Next Greater Element III.

function solve(n) {
  const digits = String(n).split('');
  let pivot = digits.length - 2;
  while (pivot >= 0 && digits[pivot] >= digits[pivot + 1]) pivot -= 1;
  if (pivot < 0) return -1;
  let swap = digits.length - 1;
  while (digits[swap] <= digits[pivot]) swap -= 1;
  [digits[pivot], digits[swap]] = [digits[swap], digits[pivot]];
  for (let left = pivot + 1, right = digits.length - 1; left < right; left += 1, right -= 1) {
    [digits[left], digits[right]] = [digits[right], digits[left]];
  }
  const answer = Number(digits.join(''));
  return answer <= 2147483647 ? answer : -1;
}

const nextGreaterElement = solve;
class Solution {
  nextGreaterElement(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreaterElement };
