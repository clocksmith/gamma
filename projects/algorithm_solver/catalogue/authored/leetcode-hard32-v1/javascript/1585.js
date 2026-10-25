'use strict';

// 1585. Check If String Is Transformable With Substring Sort Operations.
// O(10*n) time, O(n) space. Queue heads avoid linear-time Array.shift().
function solve(s, t) {
  const positions = Array.from({ length: 10 }, () => []);
  for (let index = 0; index < s.length; index += 1) positions[s.charCodeAt(index) - 48].push(index);
  const heads = new Int32Array(10);
  for (const char of t) {
    const digit = char.charCodeAt(0) - 48;
    if (heads[digit] === positions[digit].length) return false;
    const position = positions[digit][heads[digit]];
    for (let smaller = 0; smaller < digit; smaller += 1) {
      if (heads[smaller] < positions[smaller].length && positions[smaller][heads[smaller]] < position) {
        return false;
      }
    }
    heads[digit] += 1;
  }
  return true;
}

const isTransformable = solve;
class Solution {
  isTransformable(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isTransformable };
