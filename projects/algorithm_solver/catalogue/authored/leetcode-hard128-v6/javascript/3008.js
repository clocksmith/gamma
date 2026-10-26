'use strict';

// 3008. Find Beautiful Indices in the Given Array II.
// Exact KMP occurrence lists joined by a monotone distance window; O(len(s)+len(a)+len(b)) time and space.

function solve(s, a, b, k) {
  function occurrences(pattern) {
    const border = Array(pattern.length).fill(0), result = [];
    for (let i = 1; i < pattern.length; i += 1) {
      let length = border[i - 1];
      while (length > 0 && pattern[i] !== pattern[length]) length = border[length - 1];
      border[i] = length + Number(pattern[i] === pattern[length]);
    }
    let length = 0;
    for (let i = 0; i < s.length; i += 1) {
      while (length > 0 && s[i] !== pattern[length]) length = border[length - 1];
      if (s[i] === pattern[length]) length += 1;
      if (length === pattern.length) { result.push(i - length + 1); length = border[length - 1]; }
    }
    return result;
  }
  const first = occurrences(a), second = occurrences(b), answer = [];
  let index = 0;
  for (const position of first) {
    while (index < second.length && second[index] < position - k) index += 1;
    if (index < second.length && second[index] <= position + k) answer.push(position);
  }
  return answer;
}

const beautifulIndices = solve;
class Solution {
  beautifulIndices(s, a, b, k) { return solve(s, a, b, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulIndices };
