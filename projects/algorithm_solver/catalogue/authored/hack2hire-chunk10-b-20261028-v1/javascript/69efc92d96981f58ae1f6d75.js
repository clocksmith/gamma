"use strict";
// Hack2Hire 69efc92d96981f58ae1f6d75 (Design a Task Assignment System, variant 2 of 4) over an INFERRED spec; qualification unknown.

function byName(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

class TaskManager {
  constructor() {
    this.tasks = new Map(); // taskId -> [name, priority, creation number]
    this.count = 0;
  }

  addTask(timestamp, name, priority) {
    this.count += 1;
    const taskId = "taskId" + this.count;
    this.tasks.set(taskId, [name, priority, this.count]);
    return taskId;
  }

  updateTask(timestamp, taskId, name, priority) {
    const task = this.tasks.get(taskId);
    if (task === undefined) return false;
    task[0] = name; task[1] = priority;
    return true;
  }

  getTask(timestamp, taskId) {
    const task = this.tasks.get(taskId);
    return task === undefined ? "" : `${task[0]}(${task[1]})`;
  }

  ordered(nameFilter, limit) {
    const picked = [];
    for (const [id, t] of this.tasks) if (nameFilter === null || t[0].includes(nameFilter)) picked.push([t[1], t[2], id]);
    picked.sort((a, b) => b[0] - a[0] || a[1] - b[1]);
    return picked.slice(0, limit).map((x) => x[2]);
  }

  searchTasks(timestamp, nameFilter, maxResults) { return this.ordered(nameFilter, maxResults); }

  listTasksSorted(timestamp, limit) { return this.ordered(null, limit); }


}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TaskManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TaskManager(...argumentLists[0]);
  const allowed = new Set(["addTask", "updateTask", "getTask", "searchTasks", "listTasksSorted"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.TaskManager = TaskManager;
