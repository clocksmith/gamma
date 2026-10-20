class local0 {
  constructor() {
    this.heap = [];
  }
  size() {
    return this.heap.length;
  }
  isEmpty() {
    return this.heap.length === 0;
  }
  enqueue(local1) {
    let local2 = this.heap.length;
    this.heap.push(local1);
    while (local2 > 0) {
      const local3 = local2 - 1 >> 1;
      if (this.heap[local3] >= local1) break;
      this.heap[local2] = this.heap[local3];
      local2 = local3;
    }
    this.heap[local2] = local1;
  }
  dequeue() {
    if (this.isEmpty()) throw new RangeError('empty priority queue');
    const local4 = this.heap[0],
      local5 = this.heap.pop();
    if (this.heap.length) {
      let local6 = 0;
      while (2 * local6 + 1 < this.heap.length) {
        let local7 = 2 * local6 + 1;
        if (local7 + 1 < this.heap.length && this.heap[local7 + 1] > this.heap[local7]) local7++;
        if (this.heap[local7] <= local5) break;
        this.heap[local6] = this.heap[local7];
        local6 = local7;
      }
      this.heap[local6] = local5;
    }
    return local4;
  }
}
var implementation = function (p0) {
  const local8 = new local0();
  for (const local9 of p0) {
    local8.enqueue(local9);
  }
  while (local8.size() > 1) {
    const local10 = local8.dequeue();
    const local11 = local8.dequeue();
    if (local11 != local10) {
      local8.enqueue(local10 - local11);
    }
  }
  return local8.isEmpty() ? 0 : local8.dequeue();
};
function lastStoneWeight(p0) {
  if (!Array.isArray(p0) || p0.length < 0 || p0.length > 20000 || !(p0.every(x => Number.isSafeInteger(x) && x >= 0 && x <= 9007199254740991))) throw new TypeError('declared input domain');
  return implementation(JSON.parse(JSON.stringify(p0)));
}
