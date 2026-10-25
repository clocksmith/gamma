'use strict';

// 2565. Subsequence With the Minimum Score.
// O(s.length+t.length) time, O(t.length) space. Both matching pointers move only forward.
function solve(s, t) {
  const sourceSize = s.length;
  const targetSize = t.length;
  const right = new Int32Array(targetSize + 1).fill(-1);
  right[targetSize] = sourceSize;
  let position = sourceSize - 1;
  for (let index = targetSize - 1; index >= 0; index -= 1) {
    while (position >= 0 && s[position] !== t[index]) position -= 1;
    right[index] = position;
    if (position >= 0) position -= 1;
  }
  let suffix = 0;
  while (suffix < targetSize && right[suffix] < 0) suffix += 1;
  let answer = suffix;
  position = -1;
  for (let prefixSize = 1; prefixSize <= targetSize; prefixSize += 1) {
    position += 1;
    while (position < sourceSize && s[position] !== t[prefixSize - 1]) position += 1;
    if (position === sourceSize) break;
    suffix = Math.max(suffix, prefixSize);
    while (right[suffix] <= position) suffix += 1;
    answer = Math.min(answer, suffix - prefixSize);
    if (answer === 0) return 0;
  }
  return answer;
}

const minimumScore = solve;
class Solution {
  minimumScore(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumScore };
