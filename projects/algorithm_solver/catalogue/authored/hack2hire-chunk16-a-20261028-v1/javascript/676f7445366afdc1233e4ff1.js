"use strict";
// Hack2Hire 676f7445366afdc1233e4ff1 (Maximum Sprint Points Sum) over an INFERRED spec; qualification unknown.

function solve(days, k) {
  const doubled = days.concat(days);
  const m = doubled.length;
  const dayPrefix = new Float64Array(m + 1);
  const pointPrefix = new Float64Array(m + 1);
  for (let i = 0; i < m; i++) {
    const d = doubled[i];
    dayPrefix[i + 1] = dayPrefix[i] + d;
    pointPrefix[i + 1] = pointPrefix[i] + d * (d + 1) / 2;
  }
  let best = 0, left = 0;
  for (let right = days.length; right < m; right++) {
    while (dayPrefix[right + 1] - dayPrefix[left + 1] >= k) left++;
    const fullDays = dayPrefix[right + 1] - dayPrefix[left + 1];
    let value = pointPrefix[right + 1] - pointPrefix[left + 1];
    const rest = k - fullDays;
    const d = doubled[left];
    value += (d * (d + 1) - (d - rest) * (d - rest + 1)) / 2;
    if (value > best) best = value;
  }
  return best;
}

function maxSprintPoints(days, k) { return solve(days, k); }

module.exports = solve;
module.exports.maxSprintPoints = maxSprintPoints;
