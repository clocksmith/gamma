"use strict";
// Hack2Hire 68a4bbfac11d63d6052ea309 (Design Worker Management System, variant 3 of 4) over an INFERRED spec; qualification unknown.

function firstAbove(arr, x) { // first index with arr[i] > x
  let lo = 0, hi = arr.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (arr[m] > x) hi = m; else lo = m + 1; }
  return lo;
}

function byName(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

class WorkerManagementSystem {
  constructor() {
    this.workers = new Map();
  }

  addWorker(workerId, position, compensation) {
    if (this.workers.has(workerId)) return false;
    this.workers.set(workerId, {pos: position, comp: compensation, open: null, total: 0, stint: 0, pending: null, entries: [], exits: [], comps: []});
    return true;
  }

  registerWorker(workerId, timestamp) {
    const w = this.workers.get(workerId);
    if (w === undefined) return "invalid_request";
    if (w.open === null) {
      const p = w.pending;
      if (p !== null && timestamp >= p[2]) { w.pos = p[0]; w.comp = p[1]; w.pending = null; w.stint = 0; }
      w.open = [timestamp, w.comp];
    } else {
      const [start, comp] = w.open;
      w.open = null;
      w.total += timestamp - start;
      w.stint += timestamp - start;
      w.entries.push(start); w.exits.push(timestamp); w.comps.push(comp);
    }
    return "registered";
  }

  get(workerId) {
    const w = this.workers.get(workerId);
    return w === undefined ? -1 : w.total;
  }

  topNWorkers(n, position) {
    const ranked = [];
    for (const [id, w] of this.workers) if (w.pos === position) ranked.push([w.stint, id]);
    ranked.sort((a, b) => b[0] - a[0] || byName(a[1], b[1]));
    return ranked.slice(0, n).map(([t, id]) => `${id}(${t})`).join(", ");
  }

  promote(workerId, newPosition, newCompensation, startTimestamp) {
    const w = this.workers.get(workerId);
    if (w === undefined || w.pending !== null) return "invalid_request";
    w.pending = [newPosition, newCompensation, startTimestamp];
    return "success";
  }


  calcSalary(workerId, startTimestamp, endTimestamp) {
    const w = this.workers.get(workerId);
    if (w === undefined) return -1;
    const entries = w.entries, exits = w.exits, comps = w.comps, count = entries.length;
    let total = 0;
    for (let i = firstAbove(exits, startTimestamp); i < count && entries[i] < endTimestamp; i++) {
      const a = entries[i] > startTimestamp ? entries[i] : startTimestamp, b = exits[i] < endTimestamp ? exits[i] : endTimestamp;
      if (b > a) {
        total += comps[i] * (b - a);
      }
    }
    return total;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WorkerManagementSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new WorkerManagementSystem(...argumentLists[0]);
  const allowed = new Set(["addWorker", "registerWorker", "get", "topNWorkers", "promote", "calcSalary"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.WorkerManagementSystem = WorkerManagementSystem;
