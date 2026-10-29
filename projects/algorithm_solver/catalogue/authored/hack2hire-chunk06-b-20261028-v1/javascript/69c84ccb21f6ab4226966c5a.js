"use strict";
// Hack2Hire 69c84ccb21f6ab4226966c5a (Guess Number II) over an INFERRED spec; qualification unknown.

function solve(target) {
  let lo = 0, hi = 999, previous = null;
  const log = [];
  for (;;) {
    const query = lo === hi || log.length % 2 === 0 ? lo : hi;
    log.push(query);
    if (query === target) return log;
    let answer;
    if (previous === null) answer = "First";
    else {
      const a = Math.abs(query - target), b = Math.abs(previous - target);
      answer = a < b ? "Hotter" : a > b ? "Colder" : "Same";
    }
    if (query === lo) lo++; else hi--;
    if (answer === "Same") { lo = hi = Math.floor((query + previous) / 2); }
    else if (answer !== "First") {
      const twiceMid = query + previous;
      if ((answer === "Hotter") === (query > previous)) lo = Math.max(lo, Math.floor(twiceMid / 2) + 1);
      else hi = Math.min(hi, Math.floor((twiceMid + 1) / 2) - 1);
    }
    previous = query;
  }
}

function hotColdTranscript(target) { return solve(target); }

module.exports = solve;
module.exports.hotColdTranscript = hotColdTranscript;
