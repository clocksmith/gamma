'use strict';

// 331. Verify Preorder Serialization of a Binary Tree (Medium).
// Specification: https://leetcode.com/problems/verify-preorder-serialization-of-a-binary-tree/description/
function solve(preorder) {
  const tokens = preorder.split(',');
  let slots = 1;
  for (const token of tokens) {
    slots--;
    if (slots < 0) return false;
    if (token !== '#') slots += 2;
  }
  return slots === 0;
}
const isValidSerialization = solve;
class Solution { isValidSerialization(preorder) { return solve(preorder); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValidSerialization };
