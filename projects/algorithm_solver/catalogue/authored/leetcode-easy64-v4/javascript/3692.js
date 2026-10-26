'use strict';

// 3692. Majority Frequency Characters (Easy).
// Specification: https://leetcode.com/problems/majority-frequency-characters/description/
// O(n) time, O(1) alphabet space; return tied-group characters in alphabetical order.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (const character of s) counts[character.charCodeAt(0) - 97]++;
  const groupSizes = new Map();
  for (const count of counts) {
    if (count > 0) groupSizes.set(count, (groupSizes.get(count) || 0) + 1);
  }
  let bestFrequency = 0;
  let bestSize = 0;
  for (const [frequency, size] of groupSizes) {
    if (size > bestSize || (size === bestSize && frequency > bestFrequency)) {
      bestFrequency = frequency;
      bestSize = size;
    }
  }
  const result = [];
  for (let index = 0; index < 26; index++) {
    if (counts[index] === bestFrequency) result.push(String.fromCharCode(97 + index));
  }
  return result.join('');
}

const majorityFrequencyGroup = solve;
class Solution {
  majorityFrequencyGroup(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, majorityFrequencyGroup };
