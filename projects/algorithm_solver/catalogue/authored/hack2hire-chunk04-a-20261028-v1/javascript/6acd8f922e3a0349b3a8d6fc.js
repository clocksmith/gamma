"use strict";
// Hack2Hire 6acd8f922e3a0349b3a8d6fc (Transaction Incident Monitor, level 1) over an INFERRED spec; qualification unknown.

const LEVEL = 1;

function solve(logs, windowSize, ...limits) {
  const byMerchant = new Map();
  for (const line of logs) {
    const [t, merchant, code, count] = line.split(',');
    if (!byMerchant.has(merchant)) byMerchant.set(merchant, []);
    byMerchant.get(merchant).push([Number(t), Number(code), Number(count)]);
  }
  const alerts = [];
  for (const [merchant, original] of byMerchant) {
    const records = original.slice().sort((x, y) => x[0] - y[0]);
    const counts = new Map(), active = new Set(), fired = new Set();
    let head = 0, total = 0, i = 0;
    while (i < records.length) {
      const t = records[i][0], arrived = new Set();
      while (i < records.length && records[i][0] === t) {
        const rec = records[i];
        if (rec[2]) counts.set(rec[1], (counts.get(rec[1]) || 0) + rec[2]);
        total += rec[2];
        arrived.add(rec[1]);
        i++;
      }
      while (records[head][0] < t - windowSize + 1) {
        const old = records[head++];
        if (!old[2]) continue;
        const left = counts.get(old[1]) - old[2];
        total -= old[2];
        if (left === 0) counts.delete(old[1]); else counts.set(old[1], left);
      }
      let codes;
      if (LEVEL === 1) codes = arrived;
      else if (LEVEL === 2) codes = [...counts.keys()];
      else codes = new Set([...counts.keys(), ...active]);
      for (const code of codes) {
        if (code === 200) continue;
        const c = counts.get(code) || 0;
        const ok = LEVEL === 1 ? c >= limits[0] : c >= limits[0] && c * 100 >= limits[1] * total;
        if (LEVEL === 3) {
          if (ok && !active.has(code)) { active.add(code); alerts.push([t, merchant, code]); }
          else if (!ok) active.delete(code);
        } else if (ok && !fired.has(code)) { fired.add(code); alerts.push([t, merchant, code]); }
      }
    }
  }
  alerts.sort((x, y) => x[0] - y[0] || (x[1] < y[1] ? -1 : x[1] > y[1] ? 1 : 0) || x[2] - y[2]);
  return alerts.map(([t, merchant, code]) => t + ',' + merchant + ',' + code);
}

function detectIncidents(logs, windowSize, threshold) { return solve(logs, windowSize, threshold); }

module.exports = solve;
module.exports.detectIncidents = detectIncidents;
