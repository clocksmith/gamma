// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
class TaskManager {
    constructor(tasks) {
        this.tasks = new Map();
        this.heap = [];
        this.version = 0;
        for (const [user, task, priority] of tasks) this.add(user, task, priority);
    }
    static higher(a, b) {
        return a[0] > b[0] || (a[0] === b[0] && a[1] > b[1]);
    }
    push(item) {
        const heap = this.heap;
        let i = heap.length;
        heap.push(item);
        while (i > 0) {
            const p = (i - 1) >> 1;
            if (!TaskManager.higher(item, heap[p])) break;
            heap[i] = heap[p];
            i = p;
        }
        heap[i] = item;
    }
    pop() {
        const heap = this.heap;
        const first = heap[0], last = heap.pop();
        if (heap.length) {
            let i = 0;
            while (2*i + 1 < heap.length) {
                let child = 2*i + 1;
                if (child + 1 < heap.length && TaskManager.higher(heap[child+1], heap[child])) child++;
                if (!TaskManager.higher(heap[child], last)) break;
                heap[i] = heap[child];
                i = child;
            }
            heap[i] = last;
        }
        return first;
    }
    add(userId, taskId, priority) {
        const version = ++this.version;
        this.tasks.set(taskId, [userId, priority, version]);
        this.push([priority, taskId, version]);
    }
    edit(taskId, newPriority) {
        this.add(this.tasks.get(taskId)[0], taskId, newPriority);
    }
    rmv(taskId) { this.tasks.delete(taskId); }
    execTop() {
        while (this.heap.length) {
            const [priority, task, version] = this.pop();
            const current = this.tasks.get(task);
            if (current && current[2] === version) {
                this.tasks.delete(task);
                return current[0];
            }
        }
        return -1;
    }
}
function solve(operations, args) {
    let manager;
    return operations.map((operation, i) => {
        if (operation === "TaskManager") {
            manager = new TaskManager(...args[i]);
            return null;
        }
        const result = manager[operation](...args[i]);
        return result === undefined ? null : result;
    });
}
module.exports = {solve, TaskManager};
