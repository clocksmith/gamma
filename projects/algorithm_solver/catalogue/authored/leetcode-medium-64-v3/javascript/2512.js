'use strict';

// 2512. Reward Top K Students: score feedback words and break score ties by student identifier.
// O(S + n log n) expected time and O(S + n) auxiliary space for total text S; inputs are read-only.
function solve(positive_feedback, negative_feedback, report, student_id, k) {
  const positive = new Set(positive_feedback);
  const negative = new Set(negative_feedback);
  const ranked = [];
  for (let index = 0; index < report.length; index += 1) {
    let score = 0;
    for (const word of report[index].split(' ')) {
      if (positive.has(word)) score += 3;
      else if (negative.has(word)) score -= 1;
    }
    ranked.push([score, student_id[index]]);
  }
  ranked.sort((left, right) => right[0] - left[0] || left[1] - right[1]);
  return ranked.slice(0, k).map(row => row[1]);
}

const topStudents = solve;
class Solution {
  topStudents(positive_feedback, negative_feedback, report, student_id, k) { return solve(positive_feedback, negative_feedback, report, student_id, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, topStudents };
