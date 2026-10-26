'use strict';

// 3722. Lexicographically Smallest String After Reverse.
// O(n^2) time and O(n) auxiliary space; reversing one character permits the unchanged string.
function solve(s) {
  let answer = s;
  for (let length = 1; length <= s.length; length += 1) {
    const first = s.slice(0, length).split('').reverse().join('') + s.slice(length);
    const second = s.slice(0, s.length - length) + s.slice(s.length - length).split('').reverse().join('');
    if (first < answer) answer = first;
    if (second < answer) answer = second;
  }
  return answer;
}

const lexSmallest = solve;
class Solution {
  lexSmallest(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexSmallest };
