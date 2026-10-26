'use strict';

// 2055. Plates Between Candles: combine plate prefixes with the closest enclosing candles.
// O(n + q) time and O(n + q) auxiliary and result space; inputs are read-only.
function solve(s, queries) {
  const size = s.length;
  const prefix = new Int32Array(size + 1);
  const leftCandle = new Int32Array(size).fill(-1);
  const rightCandle = new Int32Array(size).fill(-1);
  let last = -1;
  for (let index = 0; index < size; index += 1) {
    prefix[index + 1] = prefix[index] + (s[index] === '*' ? 1 : 0);
    if (s[index] === '|') last = index;
    leftCandle[index] = last;
  }
  last = -1;
  for (let index = size - 1; index >= 0; index -= 1) {
    if (s[index] === '|') last = index;
    rightCandle[index] = last;
  }
  return queries.map(([left, right]) => {
    const start = rightCandle[left];
    const end = leftCandle[right];
    return start >= 0 && start < end ? prefix[end] - prefix[start] : 0;
  });
}

const platesBetweenCandles = solve;
class Solution {
  platesBetweenCandles(s, queries) { return solve(s, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, platesBetweenCandles };
