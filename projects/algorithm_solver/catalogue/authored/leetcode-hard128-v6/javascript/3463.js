'use strict';

// 3463. Check If Digits Are Equal in String After Operations II.
// Compute binomial coefficients modulo two and five with Lucas digits, then combine modulo ten; O(n log n) time and O(1) space. Input is preserved.

function solve(s) {
  const small = [[1], [1,1], [1,2,1], [1,3,3,1], [1,4,1,4,1]], top = s.length - 2;
  let difference = 0;
  for (let index = 0; index <= top; index += 1) {
    const moduloTwo = (index & (top - index)) === 0 ? 1 : 0;
    let first = top, second = index, moduloFive = 1;
    while (first || second) {
      const upper = first % 5, lower = second % 5;
      if (lower > upper) { moduloFive = 0; break; }
      moduloFive = moduloFive * small[upper][lower] % 5;
      first = Math.floor(first / 5); second = Math.floor(second / 5);
    }
    const coefficient = moduloFive % 2 === moduloTwo ? moduloFive : moduloFive + 5;
    difference = (difference + coefficient * (s.charCodeAt(index) - s.charCodeAt(index + 1))) % 10;
  }
  return difference === 0;
}

const hasSameDigits = solve;
class Solution {
  hasSameDigits(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasSameDigits };
