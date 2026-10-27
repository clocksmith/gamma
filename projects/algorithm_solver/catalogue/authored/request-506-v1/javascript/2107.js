// Original implementation. Contract: https://leetcode.com/problems/number-of-unique-flavors-after-sharing-k-candies/
"use strict";

function solve(candies, k) {
  // Counts outside the current length-k window given to the sibling.
  const remaining = new Map();
  for (let i = k; i < candies.length; i++) {
    remaining.set(candies[i], (remaining.get(candies[i]) || 0) + 1);
  }
  let answer = remaining.size;
  for (let i = k; i < candies.length; i++) {
    const restored = candies[i - k];
    remaining.set(restored, (remaining.get(restored) || 0) + 1);
    const removed = candies[i];
    const count = remaining.get(removed) - 1;
    if (count > 0) remaining.set(removed, count);
    else remaining.delete(removed);
    answer = Math.max(answer, remaining.size);
  }
  return answer;
}

module.exports = solve;
