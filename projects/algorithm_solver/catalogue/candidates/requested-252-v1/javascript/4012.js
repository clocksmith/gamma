/**
 * 4012. Count of Unfinished Tasks After Each Shift
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-of-unfinished-tasks-after-each-shift/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4012.Count%20of%20Unfinished%20Tasks%20After%20Each%20Shift/README_EN.md
 * Complexity: O(n + q log n) time, O(n) auxiliary space.
 * Completed shifts discard excess time rather than carrying a modulo remainder. Partial tasks count as unfinished; inputs preserved.
 */

function solve(tasks, shifts) {
  const prefix = [];
  let total = 0;
  for (const duration of tasks) { total += duration; prefix.push(total); }
  const answer = [];
  let spent = 0;
  for (const duration of shifts) {
    spent += duration;
    if (spent >= total) { answer.push(0); spent = 0; }
    else {
      let lo = 0, hi = prefix.length;
      while (lo < hi) { const mid = Math.floor((lo + hi) / 2); if (prefix[mid] <= spent) lo = mid + 1; else hi = mid; }
      answer.push(tasks.length - lo);
    }
  }
  return answer;
}

function countTasks(tasks, shifts) {
  return solve(tasks, shifts);
}

class Solution {
  countTasks(tasks, shifts) {
    return solve(tasks, shifts);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countTasks, Solution };
}
