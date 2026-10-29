"use strict";
// Hack2Hire 697da047b8c468a441586160 (Linked User Records by Similarity, variant 3 of 3) over an INFERRED spec; qualification unknown.

function units(text) {
  const dot = text.indexOf(".");
  const whole = dot < 0 ? text : text.slice(0, dot), frac = dot < 0 ? "" : text.slice(dot + 1);
  return Number(whole) * 10000 + Number((frac + "0000").slice(0, 4));
}

function scorer(records, weights, threshold) {
  // Exact integer weights (ten-thousandths), value buckets per weighted field, and a per-row score function.
  const header = records[0], rows = records.slice(1), fields = [];
  for (const item of weights) {
    const [name, value] = item.split(":"), w = units(value);
    if (w) fields.push([header.indexOf(name), w]);
  }
  const buckets = fields.map(([k]) => {
    const byValue = new Map();
    rows.forEach((row, j) => {
      if (row[k] !== "") { if (!byValue.has(row[k])) byValue.set(row[k], []); byValue.get(row[k]).push(j); }
    });
    return byValue;
  });
  function scores(i) {
    const score = new Array(rows.length).fill(0), row = rows[i];
    for (let f = 0; f < fields.length; f++) {
      const [k, w] = fields[f];
      if (row[k] !== "") for (const j of buckets[f].get(row[k])) score[j] += w;
    }
    return score;
  }
  return [rows, header.indexOf("id"), scores, units(String(threshold))];
}

function solve(records, weights, threshold) {
  const [rows, idc, scores, t] = scorer(records, weights, threshold), out = [];
  for (let i = 0; i < rows.length; i++) {
    const score = scores(i);
    let best = -1, pick = -1;
    for (let j = 0; j < rows.length; j++) if (j !== i && score[j] >= t && score[j] > best) { best = score[j]; pick = j; }
    out.push(pick >= 0 ? rows[pick][idc] : "");
  }
  return out;
}

function bestMatches(records, weights, threshold) { return solve(records, weights, threshold); }

module.exports = solve;
module.exports.bestMatches = bestMatches;
