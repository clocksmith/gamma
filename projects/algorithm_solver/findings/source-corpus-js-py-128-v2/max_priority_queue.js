// Explicit local dependency for the pinned Last Stone Weight source.
// Integer max heap; no package/runtime-provided queue is assumed.
class MaxPriorityQueue {
  constructor() { this.heap = []; }
  size() { return this.heap.length; }
  isEmpty() { return this.heap.length === 0; }
  enqueue(value) {
    let i = this.heap.length;
    this.heap.push(value);
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this.heap[parent] >= value) break;
      this.heap[i] = this.heap[parent];
      i = parent;
    }
    this.heap[i] = value;
  }
  dequeue() {
    if (this.isEmpty()) throw new RangeError('empty priority queue');
    const result = this.heap[0], last = this.heap.pop();
    if (this.heap.length) {
      let i = 0;
      while (2 * i + 1 < this.heap.length) {
        let child = 2 * i + 1;
        if (child + 1 < this.heap.length && this.heap[child + 1] > this.heap[child]) child++;
        if (this.heap[child] <= last) break;
        this.heap[i] = this.heap[child];
        i = child;
      }
      this.heap[i] = last;
    }
    return result;
  }
}
