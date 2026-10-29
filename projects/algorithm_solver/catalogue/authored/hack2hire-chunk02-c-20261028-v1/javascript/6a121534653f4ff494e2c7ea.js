"use strict";
// Hack2Hire 6a121534653f4ff494e2c7ea (Camera Log Relay Server, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class CameraLogServer {
  constructor() {
    this.commands = new Map(); // cameraId -> {items, head}
    this.logs = [];
    this.logHead = 0;
  }
  requestLog(cameraId, timestamp) {
    if (!this.commands.has(cameraId)) this.commands.set(cameraId, {items: [], head: 0});
    this.commands.get(cameraId).items.push(timestamp);
  }
  pollCommand(cameraId) {
    const queue = this.commands.get(cameraId);
    if (!queue || queue.head === queue.items.length) return -1;
    return queue.items[queue.head++];
  }
  sendLog(cameraId, timestamp, log) { this.logs.push([cameraId, timestamp, log]); }
  pollLog() {
    if (this.logHead === this.logs.length) return null;
    const entry = this.logs[this.logHead];
    this.logs[this.logHead++] = undefined;
    return entry;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "CameraLogServer") throw new Error("exact initial constructor required");
  const instance = new CameraLogServer(...argumentLists[0]);
  const allowed = new Set(["requestLog", "pollCommand", "sendLog", "pollLog"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.CameraLogServer = CameraLogServer;
