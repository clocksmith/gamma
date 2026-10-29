"use strict";
// Original Hack2Hire 69dd8c3595e80ae213e5b9c7 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown.
class ToDoList {
  constructor() { this.tasks = new Map(); this.requires = new Map(); this.edges = new Set(); }
  add(taskId, description, status) {
    if (!this.tasks.has(taskId)) { this.tasks.set(taskId, [taskId, description, status]); this.requires.set(taskId, []); }
  }
  get(taskId) { return this.tasks.has(taskId) ? [...this.tasks.get(taskId)] : []; }
  updateStatus(taskId, status) {
    if (!this.tasks.has(taskId)) return false;
    this.tasks.get(taskId)[2] = status;
    return true;
  }
  getDependencies(taskId) { return this.requires.has(taskId) ? [...this.requires.get(taskId)] : []; }
  addDependency(taskId, dependsOnId) {
    const key = taskId + "\n" + dependsOnId;
    if (!this.tasks.has(taskId) || !this.tasks.has(dependsOnId) || taskId === dependsOnId || this.edges.has(key)) return false;
    this.edges.add(key);
    this.requires.get(taskId).push(dependsOnId);
    return true;
  }
}
const METHODS = new Set(["add", "get", "updateStatus", "addDependency", "getDependencies"]);
function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ToDoList" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new ToDoList(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!METHODS.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.ToDoList = ToDoList;
