'use strict';

// 2121. Intervals Between Identical Elements: accumulate equal-value index distances from both directions.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(arr) {
  const answer = new Array(arr.length).fill(0);
  const counts = new Map();
  const totals = new Map();
  for (let index = 0; index < arr.length; index += 1) {
    const value = arr[index];
    const count = counts.get(value) || 0;
    const total = totals.get(value) || 0;
    answer[index] = index * count - total;
    counts.set(value, count + 1);
    totals.set(value, total + index);
  }
  counts.clear();
  totals.clear();
  for (let index = arr.length - 1; index >= 0; index -= 1) {
    const value = arr[index];
    const count = counts.get(value) || 0;
    const total = totals.get(value) || 0;
    answer[index] += total - index * count;
    counts.set(value, count + 1);
    totals.set(value, total + index);
  }
  return answer;
}

const getDistances = solve;
class Solution {
  getDistances(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getDistances };
