'use strict';

// 2007. Find Original Array From Doubled Array: pair each smallest remaining nonnegative value with its double.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(changed) {
  if (changed.length % 2) return [];
  const counts = new Map();
  for (const value of changed) counts.set(value, (counts.get(value) || 0) + 1);
  const answer = [];
  for (const value of [...changed].sort((left, right) => left - right)) {
    if (counts.get(value) === 0) continue;
    counts.set(value, counts.get(value) - 1);
    const doubled = 2 * value;
    if ((counts.get(doubled) || 0) === 0) return [];
    counts.set(doubled, counts.get(doubled) - 1);
    answer.push(value);
  }
  return answer;
}

const findOriginalArray = solve;
class Solution {
  findOriginalArray(changed) { return solve(changed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findOriginalArray };
