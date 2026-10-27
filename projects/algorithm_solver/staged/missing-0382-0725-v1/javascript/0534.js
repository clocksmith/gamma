'use strict';

// 534. Game Play Analysis III. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. activity: player_id, device_id, event_date (YYYY-MM-DD), games_played. Output: player_id, event_date, games_played_so_far.

function solve(activity) {
  const rows = activity.slice().sort((a, b) => a.player_id - b.player_id || (a.event_date < b.event_date ? -1 : a.event_date > b.event_date ? 1 : 0));
  const totals = new Map();
  return rows.map(row => {
    const total = (totals.get(row.player_id) || 0) + row.games_played;
    totals.set(row.player_id, total);
    return {player_id: row.player_id, event_date: row.event_date, games_played_so_far: total};
  });
}

const gamePlayAnalysis = solve;
class Solution {
  gamePlayAnalysis(activity) { return solve(activity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gamePlayAnalysis };
