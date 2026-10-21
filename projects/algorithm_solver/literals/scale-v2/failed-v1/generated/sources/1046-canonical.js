function solve(values) {
  if (!Array.isArray(values) || values.length < 0 || values.length > 20000 || !values.every(values2 => Number.isSafeInteger(values2) && values2 >= 0 && values2 <= 9007199254740991))
    throw new TypeError('declared input domain');
  return value2(JSON.parse(JSON.stringify(values)));
}
class value3 {
  constructor() {
    this.heap = [];
  }
  size() {
    return this.heap.length;
  }
  isEmpty() {
    return this.heap.length === 0;
  }
  enqueue(values3) {
    let value4 = this.heap.length;
    this.heap.push(values3);
    while (value4 > 0) {
      const value5 = value4 - 1 >> 1;
      if (this.heap[value5] >= values3)
        break;
      this.heap[value4] = this.heap[value5];
      value4 = value5;
    }
    this.heap[value4] = values3;
  }
  dequeue() {
    if (this.isEmpty())
      throw new RangeError('empty priority queue');
    const value6 = this.heap[0], value7 = this.heap.pop();
    if (this.heap.length) {
      let value8 = 0;
      while (2 * value8 + 1 < this.heap.length) {
        let value9 = 2 * value8 + 1;
        if (value9 + 1 < this.heap.length && this.heap[value9 + 1] > this.heap[value9])
          value9++;
        if (this.heap[value9] <= value7)
          break;
        this.heap[value8] = this.heap[value9];
        value8 = value9;
      }
      this.heap[value8] = value7;
    }
    return value6;
  }
}
var value2 = function (values4) {
  const value10 = new value();
  for (const value11 of values4) {
    value10.enqueue(value11);
  }
  while (value10.size() > 1) {
    const value12 = value10.dequeue();
    const value13 = value10.dequeue();
    if (value13 != value12) {
      value10.enqueue(value12 - value13);
    }
  }
  return value10.isEmpty() ? 0 : value10.dequeue();
};
