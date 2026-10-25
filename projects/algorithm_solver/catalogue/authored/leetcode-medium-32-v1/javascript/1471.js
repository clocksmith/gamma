'use strict';

// 1471. The k Strongest Values in an Array: take the stronger sorted endpoint with larger-value ties.
// O(n log n + k) time and O(n) auxiliary space; inputs are read-only.
function solve(arr, k) {
  const values = [...arr].sort((left, right) => left - right);
  const median = values[Math.floor((values.length - 1) / 2)];
  let left = 0;
  let right = values.length - 1;
  const answer = [];
  while (answer.length < k) {
    if (median - values[left] > values[right] - median) {
      answer.push(values[left]);
      left += 1;
    } else {
      answer.push(values[right]);
      right -= 1;
    }
  }
  return answer;
}

const getStrongest = solve;
class Solution {
  getStrongest(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getStrongest };
