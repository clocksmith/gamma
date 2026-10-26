'use strict';

// 3863. Minimum Operations to Sort a String.
// O(n) time and O(1) alphabet space; endpoint placement of global extrema determines the required proper-substring sorts.
function solve(s) {
  let sorted = true;
  let smallest = s[0];
  let largest = s[0];
  const counts = new Map();
  for (let index = 0; index < s.length; index += 1) {
    if (index > 0 && s[index - 1] > s[index]) sorted = false;
    if (s[index] < smallest) smallest = s[index];
    if (s[index] > largest) largest = s[index];
    counts.set(s[index], (counts.get(s[index]) || 0) + 1);
  }
  if (sorted) return 0;
  if (s.length === 2) return -1;
  if (s[0] === smallest || s[s.length - 1] === largest) return 1;
  if (s[0] === largest && s[s.length - 1] === smallest && counts.get(largest) === 1 && counts.get(smallest) === 1) return 3;
  return 2;
}

const minOperations = solve;
class Solution {
  minOperations(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
