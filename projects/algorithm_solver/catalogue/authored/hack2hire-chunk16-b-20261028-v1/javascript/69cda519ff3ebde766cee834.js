"use strict";
// Hack2Hire 69cda519ff3ebde766cee834 (Object Field Offset Manager) over an INFERRED spec; qualification unknown.

class ObjectLayout {
  constructor(names, sizes) {
    this.slotNames = names.slice();
    this.sizes = sizes.slice();
    this.slot = new Map();
    for (let i = 0; i < this.slotNames.length; i++) this.slot.set(this.slotNames[i], i);
    this.total = 0;
    for (const s of this.sizes) this.total += s;
    this.rebuild(Math.max(1, this.sizes.length));
  }

  rebuild(capacity) {
    this.capacity = capacity;
    const tree = new Float64Array(capacity + 1);
    for (let i = 0; i < this.sizes.length; i++) tree[i + 1] += this.sizes[i];
    for (let i = 1; i <= capacity; i++) {
      const j = i + (i & -i);
      if (j <= capacity) tree[j] += tree[i];
    }
    this.tree = tree;
  }

  add(index, delta) {
    for (let i = index + 1; i <= this.capacity; i += i & -i) this.tree[i] += delta;
  }

  before(index) {
    let total = 0;
    for (let i = index; i > 0; i -= i & -i) total += this.tree[i];
    return total;
  }

  getOffset(name) {
    const index = this.slot.get(name);
    return index === undefined ? -1 : this.before(index);
  }

  fieldAt(offset) {
    if (offset >= this.total) return "";
    let position = 0, remaining = offset, step = 1;
    while (step * 2 <= this.capacity) step *= 2;
    for (; step > 0; step = Math.floor(step / 2)) {
      const next = position + step;
      if (next <= this.capacity && this.tree[next] <= remaining) { position = next; remaining -= this.tree[next]; }
    }
    return this.slotNames[position];
  }

  totalSize() {
    return this.total;
  }

  addField(name, size) {
    if (this.slot.has(name)) return false;
    const index = this.sizes.length;
    this.slotNames.push(name);
    this.sizes.push(size);
    this.slot.set(name, index);
    this.total += size;
    if (index >= this.capacity) this.rebuild(this.capacity * 2);
    else this.add(index, size);
    return true;
  }

  removeField(name) {
    const index = this.slot.get(name);
    if (index === undefined) return false;
    this.slot.delete(name);
    this.add(index, -this.sizes[index]);
    this.total -= this.sizes[index];
    this.sizes[index] = 0;
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ObjectLayout" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new ObjectLayout(...argumentLists[0]);
  const allowed = new Set(["getOffset", "fieldAt", "totalSize", "addField", "removeField"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ObjectLayout = ObjectLayout;
