/**
 * 4001. Aggregate Two Time Series
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/aggregate-two-time-series/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4001.Aggregate%20Two%20Time%20Series/README_EN.md
 * Complexity: O(n+m) time, O(1) auxiliary space excluding output.
 * Missing timestamps take the NEXT available value, not the previous value. Inputs preserved; native method unconfirmed.
 */

function solve(series1, series2) {
  let i = 0, j = 0;
  const answer = [];
  while (i < series1.length || j < series2.length) {
    const t1 = i < series1.length ? series1[i][0] : Infinity;
    const t2 = j < series2.length ? series2[j][0] : Infinity;
    const timestamp = Math.min(t1, t2);
    const value = (i < series1.length ? series1[i][1] : 0) + (j < series2.length ? series2[j][1] : 0);
    answer.push([timestamp, value]);
    i += Number(t1 === timestamp); j += Number(t2 === timestamp);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
