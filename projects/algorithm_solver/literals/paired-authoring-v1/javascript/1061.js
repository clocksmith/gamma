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
  smallestEquivalentString(s1, s2, baseStr) {
    const groups = new DisjointSet(26);
    const firstCode = "a".charCodeAt(0);
    for (let index = 0; index < s1.length; index += 1) {
      groups.union(s1.charCodeAt(index) - firstCode, s2.charCodeAt(index) - firstCode);
    }
    const output = [];
    for (const character of baseStr) {
      const root = groups.find(character.charCodeAt(0) - firstCode);
      output.push(String.fromCharCode(firstCode + groups.minimum[root]));
    }
    return output.join("");
  }
}
