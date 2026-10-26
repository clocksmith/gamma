/**
 * 3401. Find Circular Gift Exchange Chains
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(secretSanta).
 * O(exchanges + cycles log cycles) time; O(exchanges) space.
 * A qualifying member has exactly one incoming and outgoing exchange in the supplied table. Self-gifts are not exchanges with another employee. Distinct (length,total) combinations are emitted once. chain_id is a 1-based ordinal after required sorting; its precise native convention needs coordinator confirmation.
 * Specification: https://leetcode.com/problems/find-circular-gift-exchange-chains/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3400-3499/3401.Find%20Circular%20Gift%20Exchange%20Chains/README_EN.md
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

function checkedInteger(value) {
  const integer = typeof value === 'bigint' ? value : BigInt(value);
  if (integer < -9007199254740991n || integer > 9007199254740991n) {
    throw new RangeError('Integer result exceeds the mock JSON safe-integer domain.');
  }
  return Number(integer);
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
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(secretSanta) {
  validateRows(secretSanta, {"giver_id": "int", "receiver_id": "int", "gift_value": "int"}, ["giver_id", "receiver_id"]);
  const outgoing = new Map();
  const incomingCount = new Map();
  for (const gift of secretSanta) {
    if (!outgoing.has(gift.giver_id)) outgoing.set(gift.giver_id, []);
    outgoing.get(gift.giver_id).push(gift);
    incomingCount.set(gift.receiver_id, (incomingCount.get(gift.receiver_id) || 0) + 1);
  }
  const eligible = id => outgoing.has(id) && outgoing.get(id).length === 1 && incomingCount.get(id) === 1;
  const visited = new Set();
  const combinations = new Map();
  for (const start of outgoing.keys()) {
    if (!eligible(start) || visited.has(start)) continue;
    const path = [];
    const position = new Map();
    let current = start;
    while (eligible(current) && !visited.has(current) && !position.has(current)) {
      position.set(current, path.length);
      path.push(current);
      current = outgoing.get(current)[0].receiver_id;
    }
    if (position.has(current)) {
      const cycle = path.slice(position.get(current));
      if (cycle.length >= 2) {
        let total = 0n;
        for (const id of cycle) total += BigInt(outgoing.get(id)[0].gift_value);
        const value = checkedInteger(total);
        combinations.set(JSON.stringify([cycle.length, value]), { chain_length: cycle.length, total_gift_value: value });
      }
    }
    for (const id of path) visited.add(id);
  }
  return [...combinations.values()]
    .sort((a, b) => b.chain_length - a.chain_length || b.total_gift_value - a.total_gift_value)
    .map((row, index) => ({ chain_id: index + 1, ...row }));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
