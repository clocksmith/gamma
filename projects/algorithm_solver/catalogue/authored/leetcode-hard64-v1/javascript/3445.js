'use strict';

// 3445. Maximum Difference Between Even and Odd Frequency II: eligible prefix minima indexed by two count parities.
// O(25*n) time and O(5*n) auxiliary space. Inputs are preserved.
function solve(s, k) {
  const n = s.length;
  const prefix = Array.from({ length: 5 }, () => new Int32Array(n + 1));
  for (let digit = 0; digit < 5; digit += 1) {
    for (let index = 0; index < n; index += 1) {
      prefix[digit][index + 1] = prefix[digit][index] + Number(s.charCodeAt(index) - 48 === digit);
    }
  }
  let answer = -Infinity;
  for (let first = 0; first < 5; first += 1) {
    for (let second = 0; second < 5; second += 1) {
      if (first === second) continue;
      const a = prefix[first];
      const b = prefix[second];
      const minimum = Array(4).fill(Infinity);
      let left = 0;
      for (let right = k; right <= n; right += 1) {
        while (left <= right - k && b[right] - b[left] >= 2) {
          const state = (a[left] % 2) * 2 + b[left] % 2;
          minimum[state] = Math.min(minimum[state], a[left] - b[left]);
          left += 1;
        }
        const state = ((a[right] % 2) ^ 1) * 2 + b[right] % 2;
        answer = Math.max(answer, a[right] - b[right] - minimum[state]);
      }
    }
  }
  return answer;
}

const maxDifference = solve;
class Solution {
  maxDifference(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDifference };
