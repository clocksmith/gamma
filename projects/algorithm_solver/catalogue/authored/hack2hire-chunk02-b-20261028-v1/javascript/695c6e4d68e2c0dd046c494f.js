"use strict";
// Original Hack2Hire 695c6e4d68e2c0dd046c494f variant over an INFERRED specification; qualification unknown.
function solve(liveInputStream) {
  const index = new Map(), need = [], out = [];
  for (const event of liveInputStream) {
    const body = event.slice(3), words = new Set(body.split(" "));
    if (event[0] === "Q") {
      const qid = need.length;
      need.push(words.size);
      for (const word of words) { if (!index.has(word)) index.set(word, []); index.get(word).push(qid); }
      out.push("ACK: " + body + "; ID=" + (qid + 1));
    } else {
      const hits = new Map();
      for (const word of words) for (const qid of index.get(word) || []) hits.set(qid, (hits.get(qid) || 0) + 1);
      const matched = [];
      for (const [qid, count] of hits) if (count === need[qid]) matched.push(qid);
      if (matched.length) out.push("M: " + body + "; Q=" + matched.sort((a, b) => a - b).map((q) => q + 1).join(","));
    }
  }
  return out;
}
function matchQueryLogs(liveInputStream) { return solve(liveInputStream); }
module.exports = solve;
module.exports.matchQueryLogs = matchQueryLogs;
