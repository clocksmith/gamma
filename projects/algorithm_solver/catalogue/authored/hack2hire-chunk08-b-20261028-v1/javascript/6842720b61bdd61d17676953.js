"use strict";
// Hack2Hire 6842720b61bdd61d17676953 (Spam Caller Counter) over an INFERRED spec; qualification unknown.

function daysFromCivil(y, m, d) {
  y -= m <= 2 ? 1 : 0;
  const era = Math.floor(y / 400), yoe = y - era * 400;
  const doy = Math.floor((153 * (m + (m > 2 ? -3 : 9)) + 2) / 5) + d - 1;
  const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
  return era * 146097 + doe - 719468;
}

function seconds(ts, cache) {
  let value = cache.get(ts);
  if (value === undefined) {
    value = daysFromCivil(+ts.substring(0, 4), +ts.substring(5, 7), +ts.substring(8, 10)) * 86400
      + +ts.substring(11, 13) * 3600 + +ts.substring(14, 16) * 60 + +ts.substring(17, 19);
    cache.set(ts, value);
  }
  return value;
}

function lowerBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] < x) lo = mid + 1; else hi = mid; } return lo; }
function upperBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] <= x) lo = mid + 1; else hi = mid; } return lo; }

function solve(calls, reports, window) {
  const cache = new Map(), byReceiver = new Map();
  for (const [receiver, ts] of reports) {
    if (!byReceiver.has(receiver)) byReceiver.set(receiver, []);
    byReceiver.get(receiver).push(seconds(ts, cache));
  }
  for (const times of byReceiver.values()) times.sort((a, b) => a - b);
  const totals = new Map();
  for (const [caller, receiver, ts] of calls) {
    const times = byReceiver.get(receiver);
    if (times) {
      const t = seconds(ts, cache);
      const count = upperBound(times, t + window) - lowerBound(times, t - window);
      if (count) totals.set(caller, (totals.get(caller) || 0) + count);
    }
  }
  const ranked = [...totals.entries()].sort((a, b) => (b[1] - a[1]) || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  return ranked.map(([caller, count]) => [caller, count]);
}

function countSpamCalls(calls, reports, window) { return solve(calls, reports, window); }

module.exports = solve;
module.exports.countSpamCalls = countSpamCalls;
