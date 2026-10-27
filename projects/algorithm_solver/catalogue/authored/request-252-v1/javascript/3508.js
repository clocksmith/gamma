'use strict';

class Router {
    constructor(memoryLimit) {
        this.limit = memoryLimit;
        this.queue = [];
        this.head = 0;
        this.present = new Set();
        this.destinations = new Map();
    }

    addPacket(source, destination, timestamp) {
        const key = `${source},${destination},${timestamp}`;
        if (this.present.has(key)) return false;
        if (this.queue.length - this.head === this.limit) this.forwardPacket();
        this.queue.push([source, destination, timestamp]);
        this.present.add(key);
        if (!this.destinations.has(destination)) {
            this.destinations.set(destination, { times: [], head: 0 });
        }
        this.destinations.get(destination).times.push(timestamp);
        return true;
    }

    forwardPacket() {
        if (this.head === this.queue.length) return [];
        const packet = this.queue[this.head++];
        this.present.delete(packet.join(','));
        const destination = packet[1];
        const entry = this.destinations.get(destination);
        entry.head++;
        if (entry.head === entry.times.length) {
            this.destinations.delete(destination);
        } else if (entry.head * 2 >= entry.times.length) {
            entry.times = entry.times.slice(entry.head);
            entry.head = 0;
        }
        if (this.head * 2 >= this.queue.length) {
            this.queue = this.queue.slice(this.head);
            this.head = 0;
        }
        return packet;
    }

    getCount(destination, startTime, endTime) {
        const entry = this.destinations.get(destination);
        if (!entry) return 0;
        const bound = (value, strict) => {
            let low = entry.head;
            let high = entry.times.length;
            while (low < high) {
                const mid = Math.floor((low + high) / 2);
                if (entry.times[mid] < value || (strict && entry.times[mid] === value)) {
                    low = mid + 1;
                } else high = mid;
            }
            return low;
        };
        return bound(endTime, true) - bound(startTime, false);
    }
}

function solve(operations, args) {
    const router = new Router(...args[0]);
    const output = [null];
    for (let i = 1; i < operations.length; i++) {
        output.push(router[operations[i]](...args[i]));
    }
    return output;
}
module.exports = { solve, Router };
