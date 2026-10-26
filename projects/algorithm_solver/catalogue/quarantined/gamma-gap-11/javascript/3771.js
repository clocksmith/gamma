'use strict';

// 3771. Total Score of Dungeon Runs.
// O(n log n) time and O(n) space; count eligible starting rooms for each earned point.
function solve(hp, damage, requirement) {
  const prefix = [0];
  for (const value of damage) prefix.push(prefix[prefix.length - 1] + value);
  let answer = 0;
  for (let index = 0; index < requirement.length; index += 1) {
    const threshold = prefix[index + 1] + requirement[index] - hp;
    let left = 0;
    let right = index + 1;
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (prefix[middle] < threshold) left = middle + 1;
      else right = middle;
    }
    answer += index + 1 - left;
  }
  return answer;
}

const totalScore = solve;
class Solution {
  totalScore(hp, damage, requirement) { return solve(hp, damage, requirement); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalScore };
