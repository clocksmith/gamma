/**
 * 3482. Analyze Organization Hierarchy
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(employees).
 * O(n log n) time including result sorting; O(n) space.
 * Uses iterative traversal and bottom-up accumulation. Leaves have team_size 0 and their own salary as budget. Malformed hierarchies reject rather than loop.
 * Specification: https://leetcode.com/problems/analyze-organization-hierarchy/description/
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

function solve(employees) {
  validateRows(employees, {"employee_id": "int", "employee_name": "str", "manager_id": "int?", "salary": "int", "department": "str"}, ["employee_id"]);
  if (employees.length === 0) return [];
  const byId = new Map(employees.map(row => [row.employee_id, row]));
  const children = new Map(employees.map(row => [row.employee_id, []]));
  const roots = [];
  for (const row of employees) {
    if (row.manager_id === null) roots.push(row.employee_id);
    else {
      if (!byId.has(row.manager_id)) throw new RangeError('Manager does not exist.');
      children.get(row.manager_id).push(row.employee_id);
    }
  }
  if (roots.length !== 1) throw new RangeError('Expected exactly one CEO.');
  const order = [roots[0]];
  const level = new Map([[roots[0], 1]]);
  for (let index = 0; index < order.length; index += 1) {
    const manager = order[index];
    for (const child of children.get(manager)) {
      if (level.has(child)) throw new RangeError('Cyclic organization.');
      level.set(child, level.get(manager) + 1);
      order.push(child);
    }
  }
  if (order.length !== employees.length) throw new RangeError('Organization is cyclic or disconnected.');
  const sizes = new Map();
  const budgets = new Map();
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const id = order[index];
    let size = 0;
    let budget = BigInt(byId.get(id).salary);
    for (const child of children.get(id)) {
      size += 1 + sizes.get(child);
      budget += budgets.get(child);
    }
    sizes.set(id, size);
    budgets.set(id, budget);
  }
  return employees.map(row => ({ employee_id: row.employee_id, employee_name: row.employee_name,
    level: level.get(row.employee_id), team_size: sizes.get(row.employee_id),
    budget: checkedInteger(budgets.get(row.employee_id)) }))
    .sort((a, b) => a.level - b.level || b.budget - a.budget ||
      compareText(a.employee_name, b.employee_name) || a.employee_id - b.employee_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
