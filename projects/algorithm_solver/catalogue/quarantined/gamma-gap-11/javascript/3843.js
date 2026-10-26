'use strict';

// 3843. First Element with Unique Frequency.
// O(n) expected time and space; distinguish an element frequency from the number of elements sharing it.
function solve(nums) {
  const frequencies = new Map();
  for (const value of nums) frequencies.set(value, (frequencies.get(value) || 0) + 1);
  const frequencyCounts = new Map();
  for (const count of frequencies.values()) frequencyCounts.set(count, (frequencyCounts.get(count) || 0) + 1);
  for (const value of nums) if (frequencyCounts.get(frequencies.get(value)) === 1) return value;
  return -1;
}

const firstUniqueFreq = solve;
class Solution {
  firstUniqueFreq(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, firstUniqueFreq };
