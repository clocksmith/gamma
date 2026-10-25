class ProbabilityHeap {
  constructor() {
    this.items = [];
  }

  higher(first, second) {
    return first[0] > second[0] || (first[0] === second[0] && first[1] < second[1]);
  }

  push(item) {
    this.items.push(item);
    let index = this.items.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.higher(this.items[index], this.items[parent])) {
        break;
      }
      [this.items[index], this.items[parent]] = [this.items[parent], this.items[index]];
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
        if (right < this.items.length && this.higher(this.items[right], this.items[left])) {
          child = right;
        }
        if (!this.higher(this.items[child], this.items[index])) {
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
  maxProbability(n, edges, succProb, start_node, end_node) {
    const neighbors = Array.from({length: n}, () => []);
    for (let index = 0; index < edges.length; index += 1) {
      const [first, second] = edges[index];
      const probability = succProb[index];
      neighbors[first].push([second, probability]);
      neighbors[second].push([first, probability]);
    }
    const best = Array(n).fill(0);
    best[start_node] = 1;
    const heap = new ProbabilityHeap();
    heap.push([1, start_node]);
    while (heap.items.length > 0) {
      const [probability, node] = heap.pop();
      if (probability < best[node]) {
        continue;
      }
      if (node === end_node) {
        return probability;
      }
      for (const [neighbor, edgeProbability] of neighbors[node]) {
        const candidate = probability * edgeProbability;
        if (candidate > best[neighbor]) {
          best[neighbor] = candidate;
          heap.push([candidate, neighbor]);
        }
      }
    }
    return 0;
  }
}
