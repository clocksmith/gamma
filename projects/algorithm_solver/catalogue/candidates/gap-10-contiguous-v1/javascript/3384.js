/**
 * 3384. Team Dominance by Pass Success
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(teams, passes).
 * O(players + passes + groups log groups) time; O(players + groups) space.
 * 45:00 belongs to half 1; 45:01 starts half 2. Emits observed sender-team/half groups, as in the consulted GROUP BY solution; it does not manufacture zero-pass groups. Unknown-player passes do not join.
 * Specification: https://leetcode.com/problems/team-dominance-by-pass-success/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3300-3399/3384.Team%20Dominance%20by%20Pass%20Success/README_EN.md
 */

function compareText(left, right) {
  const a = Array.from(left);
  const b = Array.from(right);
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
    const difference = a[index].codePointAt(0) - b[index].codePointAt(0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  return a.length - b.length;
}

function matchTime(value) {
  if (typeof value !== 'string' || value.length !== 5 || !/^[0-9]{2}:[0-9]{2}$/.test(value)) {
    throw new TypeError('Expected a normalized MM:SS match timestamp.');
  }
  const minutes = Number(value.slice(0, 2));
  const seconds = Number(value.slice(3));
  if (seconds > 59 || minutes > 90 || (minutes === 90 && seconds !== 0)) {
    throw new RangeError('Match timestamp is outside 00:00 through 90:00.');
  }
  return minutes * 60 + seconds;
}

function validateRows(rows, schema, primaryKey) {
  if (!Array.isArray(rows)) throw new TypeError('Expected a table as an array of row objects.');
  const seen = new Set();
  for (const row of rows) {
    if (row === null || typeof row !== 'object' || Array.isArray(row)) {
      throw new TypeError('Expected a row object.');
    }
    for (const [column, declared] of Object.entries(schema)) {
      if (!Object.prototype.hasOwnProperty.call(row, column)) throw new TypeError('Missing column: ' + column);
      const value = row[column];
      if (value === null && declared.endsWith('?')) continue;
      const kind = declared.replace(/\?$/, '');
      let valid = false;
      if (kind === 'int') valid = Number.isSafeInteger(value);
      else if (kind === 'str') valid = typeof value === 'string' && !Array.from(value).some(c => { const p = c.codePointAt(0); return p >= 0xD800 && p <= 0xDFFF; });
      else if (kind === 'time') { matchTime(value); valid = true; }
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(teams, passes) {
  validateRows(teams, {"player_id": "int", "team_name": "str"}, ["player_id"]);
  validateRows(passes, {"pass_from": "int", "time_stamp": "time", "pass_to": "int"}, ["pass_from", "time_stamp"]);
  const byPlayer = new Map(teams.map(row => [row.player_id, row.team_name]));
  const scores = new Map();
  for (const pass of passes) {
    if (!byPlayer.has(pass.pass_from) || !byPlayer.has(pass.pass_to)) continue;
    const team = byPlayer.get(pass.pass_from);
    const half = matchTime(pass.time_stamp) <= 45 * 60 ? 1 : 2;
    const key = JSON.stringify([team, half]);
    if (!scores.has(key)) scores.set(key, { team_name: team, half_number: half, dominance: 0 });
    scores.get(key).dominance += team === byPlayer.get(pass.pass_to) ? 1 : -1;
  }
  return [...scores.values()].sort((a, b) => compareText(a.team_name, b.team_name) || a.half_number - b.half_number);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
