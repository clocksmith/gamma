'use strict';

// 1104. Path In Zigzag Labelled Binary Tree (Medium).
// Specification: https://leetcode.com/problems/path-in-zigzag-labelled-binary-tree/description/
function levelOf(label) { return Math.floor(Math.log2(label)); }
function solve(label) {
  const result = [];
  let current = label;
  while (current >= 1) {
    result.push(current);
    if (current === 1) break;
    const level = levelOf(current);
    const normal = level % 2 === 1 ? 3 * (2 ** level) - 1 - current : current;
    const parentNormal = Math.floor(normal / 2);
    const parentLevel = level - 1;
    current = parentLevel % 2 === 1 ? 3 * (2 ** parentLevel) - 1 - parentNormal : parentNormal;
  }
  return result.reverse();
}
const pathInZigZagTree = solve;
class Solution { pathInZigZagTree(label) { return solve(label); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, pathInZigZagTree };
