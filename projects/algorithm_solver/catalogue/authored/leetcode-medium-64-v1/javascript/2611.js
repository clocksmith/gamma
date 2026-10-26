'use strict';

// 2611. Mice and Cheese: start with the second mouse rewards and take the k largest reassignment gains.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(reward1, reward2, k) {
  const gains = new Array(reward1.length);
  let answer = 0;
  for (let index = 0; index < reward1.length; index += 1) {
    gains[index] = reward1[index] - reward2[index];
    answer += reward2[index];
  }
  gains.sort((left, right) => right - left);
  for (let index = 0; index < k; index += 1) answer += gains[index];
  return answer;
}

const miceAndCheese = solve;
class Solution {
  miceAndCheese(reward1, reward2, k) { return solve(reward1, reward2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, miceAndCheese };
