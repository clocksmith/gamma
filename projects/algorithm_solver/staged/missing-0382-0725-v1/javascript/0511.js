'use strict';

// 511. Game Play Analysis I. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, first_login.

function solve(activity) {
  const first = new Map();
  for (const row of activity) {
    if (!first.has(row.player_id) || row.event_date < first.get(row.player_id)) {
      first.set(row.player_id, row.event_date);
    }
  }
  return [...first.keys()].sort((a, b) => a - b).map(player => ({player_id: player, first_login: first.get(player)}));
}

const gamePlayAnalysis = solve;
class Solution {
  gamePlayAnalysis(activity) { return solve(activity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gamePlayAnalysis };
