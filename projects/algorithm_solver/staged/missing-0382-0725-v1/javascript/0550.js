'use strict';

// 550. Game Play Analysis IV. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: fraction; an empty denominator yields NULL.

function _roundedRatio(numerator, denominator, places) {
  let a = BigInt(numerator);
  let b = BigInt(denominator);
  const sign = (a < 0n) !== (b < 0n) ? -1 : 1;
  if (a < 0n) a = -a;
  if (b < 0n) b = -b;
  const scale = 10n ** BigInt(places);
  const rounded = (2n * a * scale + b) / (2n * b);
  return sign * Number(rounded) / Number(scale);
}

function solve(activity) {
  const first = new Map();
  const days = new Set();
  for (const row of activity) {
    const day = Date.parse(row.event_date + 'T00:00:00Z') / 86400000;
    days.add(JSON.stringify([row.player_id, day]));
    first.set(row.player_id, Math.min(first.get(row.player_id) ?? day, day));
  }
  if (first.size === 0) return [{fraction: null}];
  let count = 0;
  for (const [player, day] of first) if (days.has(JSON.stringify([player, day + 1]))) count += 1;
  return [{fraction: _roundedRatio(count, first.size, 2)}];
}

const gamePlayAnalysis = solve;
class Solution {
  gamePlayAnalysis(activity) { return solve(activity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gamePlayAnalysis };
