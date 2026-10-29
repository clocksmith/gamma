"use strict";
// Hack2Hire 6934e59f5f306485cc5f08be (Find Duplicate Files, variant 2: chunked streams). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

const BLOCK = 64;
const byCodeUnit = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

class Stream {
  constructor(chunks) {
    this.chunks = chunks;
    this.index = 0;
    this.offset = 0;
  }
  read(n) {
    const out = [];
    while (out.length < n && this.index < this.chunks.length) {
      const chunk = this.chunks[this.index];
      const take = Math.min(n - out.length, chunk.length - this.offset);
      for (let i = 0; i < take; i++) out.push(chunk[this.offset + i]);
      this.offset += take;
      if (this.offset === chunk.length) {
        this.index++;
        this.offset = 0;
      }
    }
    return out;
  }
}

function solve(root) {
  const paths = [], streams = [], sizes = [], stack = [[root, ""]];
  while (stack.length) {
    const [node, prefix] = stack.pop();
    for (const f of node.files) {
      paths.push(prefix + "/" + f.name);
      streams.push(new Stream(f.chunks));
      let size = 0;
      for (const c of f.chunks) size += c.length;
      sizes.push(size);
    }
    for (const d of node.directories) stack.push([d, prefix + "/" + d.name]);
  }
  const bySize = new Map();
  sizes.forEach((size, i) => {
    if (!bySize.has(size)) bySize.set(size, []);
    bySize.get(size).push(i);
  });
  const groups = [];
  for (const [size, members] of bySize) {
    const work = [[members, 0]];
    while (work.length) {
      const [group, offset] = work.pop();
      if (group.length < 2) continue;
      if (offset >= size) {
        groups.push(group.map((i) => paths[i]).sort(byCodeUnit));
        continue;
      }
      const split = new Map();
      for (const i of group) {
        const key = streams[i].read(BLOCK).join(",");
        if (!split.has(key)) split.set(key, []);
        split.get(key).push(i);
      }
      for (const sub of split.values()) work.push([sub, offset + BLOCK]);
    }
  }
  return groups.sort((a, b) => byCodeUnit(a[0], b[0]));
}

function findDuplicateFiles(root) { return solve(root); }
module.exports = solve;
module.exports.findDuplicateFiles = findDuplicateFiles;
