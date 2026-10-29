"use strict";
// Hack2Hire 68a4bbf8c11d63d6052ea308 (Design Worker Management System, variant 2 of 4) over an INFERRED spec; qualification unknown.

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
      w.open = [timestamp, w.comp];
    } else {
      const [start, comp] = w.open;
      w.open = null;
      w.total += timestamp - start;
      w.stint += timestamp - start;
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


}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WorkerManagementSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new WorkerManagementSystem(...argumentLists[0]);
  const allowed = new Set(["addWorker", "registerWorker", "get", "topNWorkers"]);
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
