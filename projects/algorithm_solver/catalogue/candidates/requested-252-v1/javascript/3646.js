'use strict';

// 3646. Next Special Palindrome Number.
// Specification: https://leetcode.com/problems/next-special-palindrome-number/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(2^9 * digitLength * alphabet^2) time, O(digitLength + alphabet) working space; enumerate digit multisets, not factorial permutations.
// Inputs are not modified.
// Input n <= 1e15; candidate comparisons use exact integers. The selected successor fits the safe JS integer domain.

function solve(n) {
  const target = String(n), targetNumber = BigInt(n);
  let answer = null;
  function nextPermutation(characters) {
    let pivot = characters.length - 2;
    while (pivot >= 0 && characters[pivot] >= characters[pivot + 1]) pivot--;
    if (pivot < 0) return null;
    let successor = characters.length - 1;
    while (characters[successor] <= characters[pivot]) successor--;
    [characters[pivot], characters[successor]] = [characters[successor], characters[pivot]];
    return characters.slice(0, pivot + 1).concat(characters.slice(pivot + 1).reverse()).join('');
  }
  for (let subset = 1; subset < 512; subset++) {
    const digits = [];
    for (let digit = 1; digit <= 9; digit++) if (subset & (1 << (digit - 1))) digits.push(digit);
    const length = digits.reduce((sum, digit) => sum + digit, 0), odd = digits.filter(digit => digit % 2);
    if (odd.length > 1 || length < target.length || length > target.length + 1) continue;
    const counts = new Array(10).fill(0);
    for (const digit of digits) counts[digit] = Math.floor(digit / 2);
    const center = odd.length ? String(odd[0]) : '', halfSize = Math.floor(length / 2);
    const smallest = () => counts.map((count, digit) => String(digit).repeat(count)).join('');
    let half;
    if (length > target.length) half = smallest();
    else {
      const prefix = target.slice(0, halfSize);
      function atLeast(position) {
        if (position === halfSize) return '';
        const required = Number(prefix[position]);
        for (let digit = Math.max(1, required); digit <= 9; digit++) {
          if (counts[digit] === 0) continue;
          counts[digit]--;
          const suffix = digit > required ? smallest() : atLeast(position + 1);
          counts[digit]++;
          if (suffix !== null) return String(digit) + suffix;
        }
        return null;
      }
      half = atLeast(0);
      if (half === null) continue;
    }
    let candidate = BigInt(half + center + [...half].reverse().join(''));
    if (candidate <= targetNumber) {
      half = nextPermutation([...half]);
      if (half === null) continue;
      candidate = BigInt(half + center + [...half].reverse().join(''));
    }
    if (answer === null || candidate < answer) answer = candidate;
  }
  return Number(answer);
}

const specialPalindrome = solve;
class Solution {
  specialPalindrome(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, specialPalindrome };
