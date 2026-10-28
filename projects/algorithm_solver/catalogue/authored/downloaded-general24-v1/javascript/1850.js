'use strict';

// 1850. Minimum Adjacent Swaps to Reach the Kth Smallest Number (Medium).
// Specification: https://leetcode.com/problems/minimum-adjacent-swaps-to-reach-the-kth-smallest-number/description/
function nextPermutation(chars) {
  let i = chars.length - 2;
  while (i >= 0 && chars[i] >= chars[i + 1]) i--;
  if (i < 0) return false;
  let j = chars.length - 1;
  while (chars[j] <= chars[i]) j--;
  const tmp = chars[i]; chars[i] = chars[j]; chars[j] = tmp;
  let left = i + 1; let right = chars.length - 1;
  while (left < right) { const t = chars[left]; chars[left] = chars[right]; chars[right] = t; left++; right--; }
  return true;
}
function solve(num, k) {
  const target = num.split('');
  for (let step = 0; step < k; step++) nextPermutation(target);
  const positions = {};
  for (let i = 0; i < num.length; i++) {
    const digit = num[i];
    if (!positions[digit]) positions[digit] = [];
    positions[digit].push(i);
  }
  const used = {};
  const sequence = [];
  for (const digit of target) {
    if (!used[digit]) used[digit] = 0;
    sequence.push(positions[digit][used[digit]++]);
  }
  let inversions = 0;
  for (let i = 0; i < sequence.length; i++) {
    for (let j = i + 1; j < sequence.length; j++) { if (sequence[i] > sequence[j]) inversions++; }
  }
  return inversions;
}
const getMinSwaps = solve;
class Solution { getMinSwaps(num, k) { return solve(num, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMinSwaps };
