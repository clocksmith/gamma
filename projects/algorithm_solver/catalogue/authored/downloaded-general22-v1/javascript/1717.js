'use strict';

// 1717. Maximum Score From Removing Substrings (Medium).
// Specification: https://leetcode.com/problems/maximum-score-from-removing-substrings/description/
function removePair(s, first, second, gain) {
  const stack = [];
  let total = 0;
  for (const ch of s) {
    if (stack.length > 0 && stack[stack.length - 1] === first && ch === second) { stack.pop(); total += gain; }
    else stack.push(ch);
  }
  return [stack.join(''), total];
}
function solve(s, x, y) {
  let total = 0;
  if (x >= y) {
    let rest; [rest, total] = removePair(s, 'a', 'b', x);
    const second = removePair(rest, 'b', 'a', y);
    total += second[1];
  } else {
    let rest; [rest, total] = removePair(s, 'b', 'a', y);
    const second = removePair(rest, 'a', 'b', x);
    total += second[1];
  }
  return total;
}
const maximumGain = solve;
class Solution { maximumGain(s, x, y) { return solve(s, x, y); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumGain };
