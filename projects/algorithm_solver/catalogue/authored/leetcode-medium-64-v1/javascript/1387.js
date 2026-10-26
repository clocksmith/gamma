'use strict';

// 1387. Sort Integers by The Power Value: memoize Collatz lengths iteratively and sort by length then value.
// O(T + m log m) time and O(T + m) space for m values and T newly visited Collatz states; inputs are read-only.
function solve(lo, hi, k) {
  const lengths = new Map([[1, 0]]);
  function power(value) {
    const path = [];
    let current = value;
    while (!lengths.has(current)) {
      path.push(current);
      current = current % 2 === 0 ? current / 2 : 3 * current + 1;
    }
    let steps = lengths.get(current);
    for (let index = path.length - 1; index >= 0; index -= 1) {
      steps += 1;
      lengths.set(path[index], steps);
    }
    return lengths.get(value);
  }
  const ordered = [];
  for (let value = lo; value <= hi; value += 1) ordered.push([power(value), value]);
  ordered.sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  return ordered[k - 1][1];
}

const getKth = solve;
class Solution {
  getKth(lo, hi, k) { return solve(lo, hi, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getKth };
