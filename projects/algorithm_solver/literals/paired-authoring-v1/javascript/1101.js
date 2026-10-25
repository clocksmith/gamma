class DisjointSet {
  constructor(count) {
    this.parent = Array.from({length: count}, (_, index) => index);
    this.size = Array(count).fill(1);
    this.minimum = Array.from({length: count}, (_, index) => index);
    this.components = count;
  }

  find(item) {
    while (this.parent[item] !== item) {
      this.parent[item] = this.parent[this.parent[item]];
      item = this.parent[item];
    }
    return item;
  }

  union(first, second) {
    let firstRoot = this.find(first);
    let secondRoot = this.find(second);
    if (firstRoot === secondRoot) {
      return false;
    }
    if (this.size[firstRoot] < this.size[secondRoot]) {
      [firstRoot, secondRoot] = [secondRoot, firstRoot];
    }
    this.parent[secondRoot] = firstRoot;
    this.size[firstRoot] += this.size[secondRoot];
    this.minimum[firstRoot] = Math.min(this.minimum[firstRoot], this.minimum[secondRoot]);
    this.components -= 1;
    return true;
  }
}


class Solution {
  earliestAcq(logs, n) {
    const groups = new DisjointSet(n);
    const ordered = logs.slice().sort((first, second) => first[0] - second[0]);
    for (const [timestamp, first, second] of ordered) {
      groups.union(first, second);
      if (groups.components === 1) {
        return timestamp;
      }
    }
    return -1;
  }
}
