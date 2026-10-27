'use strict';

// 578. Get Highest Answer Rate Question. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. survey_log: id, action, question_id, answer_id, q_num, timestamp. Output: survey_log. Counts retain duplicate rows; zero-show ratios sort as SQL NULL after numeric ratios.

function solve(survey_log) {
  const counts = new Map();
  for (const row of survey_log) {
    if (!counts.has(row.question_id)) counts.set(row.question_id, [0n, 0n]);
    const pair = counts.get(row.question_id);
    if (row.action === 'answer') pair[0] += 1n;
    if (row.action === 'show') pair[1] += 1n;
  }
  let best = null;
  for (const question of [...counts.keys()].sort((a, b) => a - b)) {
    const [answer, show] = counts.get(question);
    if (best === null) best = question;
    else {
      const [oldAnswer, oldShow] = counts.get(best);
      if (show > 0n && (oldShow === 0n || answer * oldShow > oldAnswer * show)) best = question;
    }
  }
  return best === null ? [] : [{survey_log: best}];
}

const highestAnswerRate = solve;
class Solution {
  highestAnswerRate(survey_log) { return solve(survey_log); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, highestAnswerRate };
