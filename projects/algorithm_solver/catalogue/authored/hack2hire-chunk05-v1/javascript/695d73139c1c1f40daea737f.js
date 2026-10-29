// Original hack2hire:695d73139c1c1f40daea737f; inferred public-preview contract; qualification unknown.
"use strict";
function _node() { return {edges: new Map(), terminal:false, value:null}; }
class RadixCache {
  constructor() { this.root = _node(); }
  insert(sequence, value) {
    const key = sequence.slice(); let node = this.root, position = 0;
    while (position < key.length) {
      const edge = node.edges.get(key[position]);
      if (!edge) { const leaf = _node(); leaf.terminal = true; leaf.value = value; node.edges.set(key[position], [key.slice(position), leaf]); return; }
      const [label, child] = edge; let common = 0;
      while (common < label.length && position+common < key.length && label[common] === key[position+common]) common++;
      if (common === label.length) { node = child; position += common; continue; }
      const middle = _node(); middle.edges.set(label[common], [label.slice(common), child]); node.edges.set(label[0], [label.slice(0,common), middle]); position += common;
      if (position === key.length) { middle.terminal = true; middle.value = value; }
      else { const leaf = _node(); leaf.terminal = true; leaf.value = value; middle.edges.set(key[position], [key.slice(position), leaf]); }
      return;
    }
    node.terminal = true; node.value = value;
  }
  get(sequence) {
    let node = this.root, position = 0;
    while (position < sequence.length) {
      const edge = node.edges.get(sequence[position]); if (!edge) return null;
      const [label, child] = edge;
      if (position+label.length > sequence.length || label.some((v,i) => v !== sequence[position+i])) return null;
      position += label.length; node = child;
    }
    return node.terminal ? node.value : null;
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "RadixCache") throw new Error("exact constructor trace required");
  const instance = new RadixCache(...argumentLists[0]), result = [null], allowed = new Set(["insert", "get"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.RadixCache = RadixCache;
