"use strict";
// Hack2Hire 6acd79422e3a0349b3a8d5be (Deployment Window Scheduler, variant 1) over an INFERRED spec; qualification unknown.
const WEEK = 10080;
function solve(inputCsv) {
  const allowed = new Int32Array(WEEK + 1), freeze = new Int32Array(WEEK + 1);
  for (const record of inputCsv) {
    const [start, end, kind] = record.split(","), delta = kind === "allowed" ? allowed : freeze;
    delta[Number(start)] += 1;
    delta[Number(end)] -= 1;
  }
  let total = 0, covered = 0, frozen = 0;
  for (let minute = 0; minute < WEEK; minute++) {
    covered += allowed[minute];
    frozen += freeze[minute];
    if (covered > 0 && frozen === 0) total++;
  }
  return total;
}
function deployableMinutes(inputCsv) { return solve(inputCsv); }
module.exports = solve;
module.exports.deployableMinutes = deployableMinutes;
