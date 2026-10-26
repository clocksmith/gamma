'use strict';

// 3747. Count Distinct Integers After Removing Zeros.
// O(log n) digit steps and O(log n) space; count exactly the positive zero-free integers <= n.
function solve(n) {
  const digits = String(n);
  const length = digits.length;
  const powers = [1];
  for (let count = 1; count <= length; count += 1) powers.push(powers[count - 1] * 9);
  let answer = 0;
  for (let count = 1; count < length; count += 1) answer += powers[count];
  for (let index = 0; index < length; index += 1) {
    const digit = Number(digits[index]);
    if (digit === 0) return answer;
    answer += (digit - 1) * powers[length - index - 1];
  }
  return answer + 1;
}

const countDistinct = solve;
class Solution {
  countDistinct(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDistinct };
