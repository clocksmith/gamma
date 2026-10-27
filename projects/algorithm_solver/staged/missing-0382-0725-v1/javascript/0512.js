'use strict';

// 512. Game Play Analysis II. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, device_id.

function solve(activity) {
  const first = new Map();
  for (const row of activity) {
    if (!first.has(row.player_id) || row.event_date < first.get(row.player_id).event_date) {
      first.set(row.player_id, row);
    }
  }
  return [...first.keys()].sort((a, b) => a - b).map(player => ({player_id: player, device_id: first.get(player).device_id}));
}

const gamePlayAnalysis = solve;
class Solution {
  gamePlayAnalysis(activity) { return solve(activity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gamePlayAnalysis };
