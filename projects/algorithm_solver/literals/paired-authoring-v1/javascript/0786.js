class FractionHeap {
  constructor(values) {
    this.values = values;
    this.items = [];
    for (let denominator = 1; denominator < values.length; denominator += 1) {
      this.items.push([0, denominator]);
    }
    for (let index = Math.floor(this.items.length / 2) - 1; index >= 0; index -= 1) {
      this.siftDown(index);
    }
  }

  less(left, right) {
    const left_product = this.values[left[0]] * this.values[right[1]];
    const right_product = this.values[right[0]] * this.values[left[1]];
    if (left_product !== right_product) {
      return left_product < right_product;
    }
    return left[0] < right[0] || (left[0] === right[0] && left[1] < right[1]);
  }

  siftDown(index) {
    while (2 * index + 1 < this.items.length) {
      let child = 2 * index + 1;
      if (child + 1 < this.items.length && this.less(this.items[child + 1], this.items[child])) {
        child += 1;
      }
      if (!this.less(this.items[child], this.items[index])) {
        break;
      }
      const saved = this.items[index];
      this.items[index] = this.items[child];
      this.items[child] = saved;
      index = child;
    }
  }

  push(item) {
    this.items.push(item);
    let index = this.items.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(this.items[index], this.items[parent])) {
        break;
      }
      const saved = this.items[index];
      this.items[index] = this.items[parent];
      this.items[parent] = saved;
      index = parent;
    }
  }

  pop() {
    const first = this.items[0];
    const last = this.items.pop();
    if (this.items.length > 0) {
      this.items[0] = last;
      this.siftDown(0);
    }
    return first;
  }
}

class Solution {
  kthSmallestPrimeFraction(arr, k) {
    const heap = new FractionHeap(arr);
    for (let rank = 1; rank <= k; rank += 1) {
      const [numerator, denominator] = heap.pop();
      if (rank === k) {
        return [arr[numerator], arr[denominator]];
      }
      if (numerator + 1 < denominator) {
        heap.push([numerator + 1, denominator]);
      }
    }
  }
}
