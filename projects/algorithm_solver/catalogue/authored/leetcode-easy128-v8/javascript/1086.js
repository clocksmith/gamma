'use strict';

// 1086. High Five (Easy).
// Specification: https://leetcode.com/problems/high-five/description/
// O(n + u log u) time, O(u) space; retain five highest scores per ID and floor averages.
function solve(items) {
  const scores = new Map();
  for (const [student, score] of items) {
    if (!scores.has(student)) scores.set(student, []);
    const best = scores.get(student);
    best.push(score);
    best.sort((a, b) => b - a);
    if (best.length > 5) best.pop();
  }
  const students = Array.from(scores.keys()).sort((a, b) => a - b);
  return students.map(student => {
    let total = 0;
    for (const score of scores.get(student)) total += score;
    return [student, Math.floor(total / 5)];
  });
}

const highFive = solve;
class Solution {
  highFive(items) { return solve(items); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, highFive };
