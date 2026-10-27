'use strict';

// 635. Design Log Storage System.

class LogSystem {
  constructor() { this.logs = []; }
  put(id, timestamp) { this.logs.push([id, timestamp]); }
  retrieve(start, end, granularity) {
    const length = {Year: 4, Month: 7, Day: 10, Hour: 13, Minute: 16, Second: 19}[granularity];
    const low = start.slice(0, length), high = end.slice(0, length);
    return this.logs.filter(([, timestamp]) => {
      const value = timestamp.slice(0, length); return value >= low && value <= high;
    }).map(([id]) => id);
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new LogSystem(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = LogSystem;

if (typeof module !== 'undefined') module.exports = { solve, LogSystem, Solution };
