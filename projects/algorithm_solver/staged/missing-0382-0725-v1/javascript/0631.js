'use strict';

// 631. Design Excel Sum Formula.

class Excel {
  constructor(height, width) { this.height = height; this.width = width.charCodeAt(0) - 64; this.values = new Map(); this.formulas = new Map(); }
  _key(row, column) { return (row - 1) * this.width + column.charCodeAt(0) - 65; }
  _cell(address) { return [Number(address.slice(1)), address[0]]; }
  set(row, column, val) {
    const key = this._key(row, column); this.formulas.delete(key); this.values.set(key, val);
  }
  get(row, column) {
    const memo = new Map();
    const evaluate = key => {
      if (memo.has(key)) return memo.get(key);
      let result = 0;
      if (!this.formulas.has(key)) result = this.values.get(key) || 0;
      else for (const [dependency, count] of this.formulas.get(key)) result += count * evaluate(dependency);
      memo.set(key, result); return result;
    };
    return evaluate(this._key(row, column));
  }
  sum(row, column, numbers) {
    const dependencies = new Map();
    const add = key => dependencies.set(key, (dependencies.get(key) || 0) + 1);
    for (const expression of numbers) {
      if (!expression.includes(':')) {
        const [r, c] = this._cell(expression); add(this._key(r, c));
      } else {
        const [first, last] = expression.split(':'), [r1, c1] = this._cell(first), [r2, c2] = this._cell(last);
        for (let r = r1; r <= r2; r += 1) for (let c = c1.charCodeAt(0); c <= c2.charCodeAt(0); c += 1) add(this._key(r, String.fromCharCode(c)));
      }
    }
    const key = this._key(row, column);
    this.formulas.set(key, dependencies); this.values.delete(key);
    return this.get(row, column);
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Excel(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = Excel;

if (typeof module !== 'undefined') module.exports = { solve, Excel, Solution };
