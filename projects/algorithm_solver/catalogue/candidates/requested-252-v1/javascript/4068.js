'use strict';

// 4068. Maximize Meeting Earnings with Idle Gaps.
// Specification: https://leetcode.com/problems/maximize-meeting-earnings-with-idle-gaps/description/
// O(n log n) time and O(n) space; half-open meetings, idle revenue only between selected meetings. Inputs are preserved.
function solve(meetings) {
  const ordered = meetings.map(meeting => meeting.slice()).sort((a, b) => a[1] - b[1]);
  const bestMinusEnd = new Float64Array(ordered.length);
  let answer = 0;
  for (let index = 0; index < ordered.length; index++) {
    const [start, end, revenue] = ordered[index];
    let left = 0;
    let right = index;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (ordered[middle][1] <= start) left = middle + 1; else right = middle;
    }
    const ending = revenue + Math.max(0, left > 0 ? start + bestMinusEnd[left - 1] : -Infinity);
    answer = Math.max(answer, ending);
    bestMinusEnd[index] = Math.max(ending - end, index > 0 ? bestMinusEnd[index - 1] : -Infinity);
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
