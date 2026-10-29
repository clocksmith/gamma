"use strict";
// Hack2Hire 69efc8ea96981f58ae1f6d74 (Design a Task Assignment System, variant 1 of 4) over an INFERRED spec; qualification unknown.

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


}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TaskManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TaskManager(...argumentLists[0]);
  const allowed = new Set(["addTask", "updateTask", "getTask"]);
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
