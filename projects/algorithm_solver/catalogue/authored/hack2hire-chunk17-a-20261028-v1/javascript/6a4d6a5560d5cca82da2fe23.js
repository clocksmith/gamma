"use strict";
// Hack2Hire 6a4d6a5560d5cca82da2fe23 (Typed Task Lock) over an INFERRED spec; qualification unknown.

class MutexTaskLock {
  constructor() {
    this.running = 0;
    this.kind = null;
    this.waitIds = [];
    this.waitTypes = [];
    this.head = 0;
  }

  acquire(jobId, jobType) {
    if (this.head === this.waitIds.length && (this.running === 0 || this.kind === jobType)) {
      this.running++;
      this.kind = jobType;
      return true;
    }
    this.waitIds.push(jobId);
    this.waitTypes.push(jobType);
    return false;
  }

  release(jobId) {
    this.running--;
    const admitted = [];
    if (this.running === 0 && this.head < this.waitIds.length) {
      this.kind = this.waitTypes[this.head];
      while (this.head < this.waitIds.length && this.waitTypes[this.head] === this.kind) admitted.push(this.waitIds[this.head++]);
      this.running = admitted.length;
    }
    return admitted;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MutexTaskLock" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new MutexTaskLock(...argumentLists[0]);
  const allowed = new Set(["acquire", "release"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.MutexTaskLock = MutexTaskLock;
