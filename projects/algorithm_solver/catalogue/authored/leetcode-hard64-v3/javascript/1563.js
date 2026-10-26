'use strict';

// 1563. Stone Game V: monotone split boundaries and interval maxima for positive stones; O(n^2) time and space.

function solve(stoneValue) {
  const size = stoneValue.length;
  const prefix = Array(size + 1).fill(0);
  for (let index = 0; index < size; index += 1) prefix[index + 1] = prefix[index] + stoneValue[index];
  const leftBest = Array.from({ length: size }, () => Array(size).fill(0));
  const rightBest = Array.from({ length: size }, () => Array(size).fill(0));
  let answer = 0;
  for (let left = size - 1; left >= 0; left -= 1) {
    leftBest[left][left] = stoneValue[left];
    rightBest[left][left] = stoneValue[left];
    let split = left - 1;
    for (let right = left + 1; right < size; right += 1) {
      const total = prefix[right + 1] - prefix[left];
      while (split + 1 < right && 2 * (prefix[split + 2] - prefix[left]) <= total) split += 1;
      let best = split >= left ? leftBest[left][split] : 0;
      const equal = split >= left && 2 * (prefix[split + 1] - prefix[left]) === total;
      const rightStart = equal ? split + 1 : split + 2;
      if (rightStart <= right) best = Math.max(best, rightBest[rightStart][right]);
      leftBest[left][right] = Math.max(leftBest[left][right - 1], total + best);
      rightBest[left][right] = Math.max(rightBest[left + 1][right], total + best);
      if (left === 0 && right === size - 1) answer = best;
    }
  }
  return answer;
}

const stoneGameV = solve;
class Solution {
  stoneGameV(stoneValue) { return solve(stoneValue); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stoneGameV };
