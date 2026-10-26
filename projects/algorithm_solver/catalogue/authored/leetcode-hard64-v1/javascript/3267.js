'use strict';

// 3267. Count Almost Equal Pairs II: enumerate up to two digit swaps and count earlier values.
// O(n log n + n*d^4) expected time and O(n + d^4) auxiliary space, d<=7. Inputs are preserved.
function solve(nums) {
  const frequency = new Map();
  let answer = 0;
  for (const number of nums.slice().sort((a, b) => a - b)) {
    const digits = Array.from(String(number), character => Number(character));
    const width = digits.length;
    const powers = Array.from({ length: width }, (_, index) => 10 ** (width - index - 1));
    const variants = new Set([number]);
    for (let left = 0; left < width; left += 1) {
      for (let right = left + 1; right < width; right += 1) {
        if (digits[left] === digits[right]) continue;
        const first = number + (digits[right] - digits[left]) * (powers[left] - powers[right]);
        variants.add(first);
        [digits[left], digits[right]] = [digits[right], digits[left]];
        for (let secondLeft = 0; secondLeft < width; secondLeft += 1) {
          for (let secondRight = secondLeft + 1; secondRight < width; secondRight += 1) {
            variants.add(first + (digits[secondRight] - digits[secondLeft])
              * (powers[secondLeft] - powers[secondRight]));
          }
        }
        [digits[left], digits[right]] = [digits[right], digits[left]];
      }
    }
    for (const value of variants) answer += frequency.get(value) || 0;
    frequency.set(number, (frequency.get(number) || 0) + 1);
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
