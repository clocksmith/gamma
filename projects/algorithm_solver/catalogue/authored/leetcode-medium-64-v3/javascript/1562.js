'use strict';

// 1562. Find Latest Group of Size M: merge adjacent one-runs using their boundary lengths.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(arr, m) {
  const lengths = new Int32Array(arr.length + 2);
  let groups = 0;
  let latest = -1;
  for (let index = 0; index < arr.length; index += 1) {
    const position = arr[index];
    const left = lengths[position - 1];
    const right = lengths[position + 1];
    if (left === m) groups -= 1;
    if (right === m) groups -= 1;
    const merged = left + right + 1;
    lengths[position - left] = merged;
    lengths[position + right] = merged;
    if (merged === m) groups += 1;
    if (groups > 0) latest = index + 1;
  }
  return latest;
}

const findLatestStep = solve;
class Solution {
  findLatestStep(arr, m) { return solve(arr, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLatestStep };
