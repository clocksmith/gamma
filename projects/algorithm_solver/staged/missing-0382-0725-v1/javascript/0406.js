'use strict';

// 406. Queue Reconstruction by Height. Insert descending heights at their required rank; preserves input arrays.

function solve(people) {
  const ordered = people.map(person => person.slice()).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const answer = [];
  for (const person of ordered) answer.splice(person[1], 0, person);
  return answer;
}

const reconstructQueue = solve;
class Solution {
  reconstructQueue(people) { return solve(people); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reconstructQueue };
