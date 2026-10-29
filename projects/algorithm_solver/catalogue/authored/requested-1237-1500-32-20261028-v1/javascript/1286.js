"use strict";

class CombinationIterator {
  constructor(characters, combinationLength) {
    this.chars = characters;
    this.n = characters.length;
    this.k = combinationLength;
    this.idx = Array.from({ length: combinationLength }, (_, i) => i);
    this.hasMore = true;
  }
  next() {
    let res = "";
    for (let i = 0; i < this.k; i++) res += this.chars[this.idx[i]];
    let i = this.k - 1;
    while (i >= 0 && this.idx[i] === this.n - this.k + i) i--;
    if (i < 0) {
      this.hasMore = false;
    } else {
      this.idx[i]++;
      for (let j = i + 1; j < this.k; j++) this.idx[j] = this.idx[j - 1] + 1;
    }
    return res;
  }
  hasNext() {
    return this.hasMore;
  }
}

function solve(operation_names, argument_lists) {
  const inst = new CombinationIterator(argument_lists[0][0], argument_lists[0][1]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    out.push(operation_names[i] === "next" ? inst.next() : inst.hasNext());
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.CombinationIterator = CombinationIterator;
