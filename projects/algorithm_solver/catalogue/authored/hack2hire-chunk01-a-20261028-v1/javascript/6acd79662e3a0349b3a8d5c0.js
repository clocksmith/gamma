"use strict";
// Hack2Hire 6acd79662e3a0349b3a8d5c0 (Deployment Window Scheduler, variant 2) over an INFERRED spec; qualification unknown.
const WEEK = 10080;
function solve(inputCsv) {
  const allowed = new Int32Array(WEEK + 1), freeze = new Int32Array(WEEK + 1);
  for (const record of inputCsv) {
    const [start, end, kind] = record.split(","), delta = kind === "allowed" ? allowed : freeze;
    delta[Number(start)] += 1;
    delta[Number(end)] -= 1;
  }
  const result = [];
  let covered = 0, frozen = 0, openAt = null;
  for (let minute = 0; minute <= WEEK; minute++) {
    if (minute < WEEK) { covered += allowed[minute]; frozen += freeze[minute]; }
    const ok = minute < WEEK && covered > 0 && frozen === 0;
    if (ok && openAt === null) openAt = minute;
    else if (!ok && openAt !== null) { result.push([openAt, minute]); openAt = null; }
  }
  return result;
}
function deployableWindows(inputCsv) { return solve(inputCsv); }
module.exports = solve;
module.exports.deployableWindows = deployableWindows;
