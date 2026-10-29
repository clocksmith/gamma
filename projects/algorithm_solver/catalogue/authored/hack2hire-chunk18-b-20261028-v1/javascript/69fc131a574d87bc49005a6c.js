"use strict";
// Hack2Hire 69fc131a574d87bc49005a6c (Data Labeling Task Scheduler, variant 2 of 2) over an INFERRED spec; qualification unknown.

function parse_(label, letter, top) {
  if (label.length < 2 || label[0] !== letter || label[1] === "0") return 0;
  let value = 0;
  for (let i = 1; i < label.length; i++) {
    const d = label.charCodeAt(i) - 48;
    if (d < 0 || d > 9) return 0;
    value = value * 10 + d;
  }
  return value <= top ? value : 0;
}

function solve(totalTask, totalModel, totalHuman, k, schedule) {
  const counts = new Array(totalTask + 1).fill(0);
  const humans = new Set(), models = new Set();
  for (const triple of schedule) {
    const t = parse_(triple[0], "t", totalTask), m = parse_(triple[1], "m", totalModel), h = parse_(triple[2], "h", totalHuman);
    if (!t || !m || !h) return false;
    const th = t * 100001 + h, tm = t * 100001 + m;
    if (humans.has(th) || models.has(tm)) return false;
    humans.add(th);
    models.add(tm);
    counts[t] += 1;
  }
  for (let t = 1; t <= totalTask; t++) if (counts[t] !== k) return false;
  return true;
}

function isValidSchedule(totalTask, totalModel, totalHuman, k, schedule) { return solve(totalTask, totalModel, totalHuman, k, schedule); }

module.exports = solve;
module.exports.isValidSchedule = isValidSchedule;
