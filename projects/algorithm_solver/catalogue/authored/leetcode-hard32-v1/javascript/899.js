'use strict';

// 899. Orderly Queue.
// O(n) minimum rotation for k=1; O(n log n) sorting otherwise; O(n) space.
function solve(s, k) {
  if (k > 1) return s.split('').sort().join('');
  const size = s.length;
  const doubled = s + s;
  let first = 0;
  let second = 1;
  let offset = 0;
  while (first < size && second < size && offset < size) {
    const left = doubled[first + offset];
    const right = doubled[second + offset];
    if (left === right) {
      offset += 1;
      continue;
    }
    if (left > right) {
      first += offset + 1;
      if (first === second) first += 1;
    } else {
      second += offset + 1;
      if (first === second) second += 1;
    }
    offset = 0;
  }
  const start = Math.min(first, second);
  return doubled.slice(start, start + size);
}

const orderlyQueue = solve;
class Solution {
  orderlyQueue(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, orderlyQueue };
