'use strict';

// 481. Magical String (Medium).
// Specification: https://leetcode.com/problems/magical-string/description/
function solve(n) {
  if (n === 0) return 0;
  const sequence = [1, 2, 2];
  let index = 2;
  while (sequence.length < n) {
    const count = sequence[index];
    const nextValue = sequence[sequence.length - 1] === 1 ? 2 : 1;
    for (let i = 0; i < count && sequence.length < n; i++) sequence.push(nextValue);
    index++;
  }
  let ones = 0;
  for (let i = 0; i < n; i++) { if (sequence[i] === 1) ones++; }
  return ones;
}
const magicalString = solve;
class Solution { magicalString(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, magicalString };
