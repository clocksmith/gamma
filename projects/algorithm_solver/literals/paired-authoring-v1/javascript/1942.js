class MinimumHeap {
  constructor() {
    this.items = [];
  }

  push(value) {
    this.items.push(value);
    let index = this.items.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.items[parent] <= this.items[index]) {
        break;
      }
      [this.items[parent], this.items[index]] = [this.items[index], this.items[parent]];
      index = parent;
    }
  }

  pop() {
    const result = this.items[0];
    const last = this.items.pop();
    if (this.items.length > 0) {
      this.items[0] = last;
      let index = 0;
      while (true) {
        const left = 2 * index + 1;
        if (left >= this.items.length) {
          break;
        }
        const right = left + 1;
        let child = left;
        if (right < this.items.length && this.items[right] < this.items[left]) {
          child = right;
        }
        if (this.items[index] <= this.items[child]) {
          break;
        }
        [this.items[index], this.items[child]] = [this.items[child], this.items[index]];
        index = child;
      }
    }
    return result;
  }
}


class Solution {
  smallestChair(times, targetFriend) {
    const events = [];
    for (let friend = 0; friend < times.length; friend += 1) {
      const [arrival, departure] = times[friend];
      events.push([arrival, 1, friend]);
      events.push([departure, 0, friend]);
    }
    events.sort((first, second) => first[0] - second[0] || first[1] - second[1] || first[2] - second[2]);
    const assigned = Array(times.length).fill(-1);
    const available = new MinimumHeap();
    let nextChair = 0;
    for (const [, kind, friend] of events) {
      if (kind === 0) {
        available.push(assigned[friend]);
      } else {
        let chair;
        if (available.items.length > 0) {
          chair = available.pop();
        } else {
          chair = nextChair;
          nextChair += 1;
        }
        assigned[friend] = chair;
        if (friend === targetFriend) {
          return chair;
        }
      }
    }
    return -1;
  }
}
