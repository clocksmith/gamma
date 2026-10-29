"use strict";
// Hack2Hire 68c48c55e558bc07a7541e31 (Snake Game) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.

const STEP = {U: [-1, 0], D: [1, 0], L: [0, -1], R: [0, 1]};

class SnakeGame {
  constructor(rows, cols) {
    this.rows = rows; this.cols = cols;
    this.body = [0]; this.head = 0;        // queue: body[head..] from tail to head cell
    this.occupied = new Set([0]);
    this.row = 0; this.col = 0; this.moves = 0; this.alive = true;
  }

  move(direction) {
    if (!this.alive) return false;
    this.moves++;
    const [dr, dc] = STEP[direction], r = this.row + dr, c = this.col + dc;
    if (r < 0 || r >= this.rows || c < 0 || c >= this.cols) { this.alive = false; return false; }
    if (this.moves % 5 !== 0) this.occupied.delete(this.body[this.head++]);
    const cell = r * this.cols + c;
    if (this.occupied.has(cell)) { this.alive = false; return false; }
    if (this.head > 4096 && this.head * 2 > this.body.length) { this.body = this.body.slice(this.head); this.head = 0; }
    this.body.push(cell); this.occupied.add(cell);
    this.row = r; this.col = c;
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SnakeGame" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new SnakeGame(...argumentLists[0]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "move") throw new Error("unknown method");
    result.push(instance.move(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.SnakeGame = SnakeGame;
