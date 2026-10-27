'use strict';
// 251. Flatten 2D Vector.
class Vector2D {
  constructor(vec) { this.vector = vec; this.row = 0; this.column = 0; this.advance(); }
  advance() {
    while (this.row < this.vector.length && this.column === this.vector[this.row].length) {
      this.row += 1; this.column = 0;
    }
  }
  next() { const value = this.vector[this.row][this.column++]; this.advance(); return value; }
  hasNext() { return this.row < this.vector.length; }
}
function solve(vec, operations) {
  const iterator = new Vector2D(vec);
  return operations.map(operation => iterator[operation]());
}
if (typeof module !== 'undefined') module.exports = { solve, Vector2D };
