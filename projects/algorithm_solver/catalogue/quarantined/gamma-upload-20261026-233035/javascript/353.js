'use strict';
// 353. Design Snake Game.
class SnakeGame {
  constructor(width, height, food) {
    this.width = width; this.height = height; this.food = food; this.foodIndex = 0;
    this.body = [[0, 0]]; this.occupied = new Set(['0:0']);
    this.directions = { U: [-1, 0], D: [1, 0], L: [0, -1], R: [0, 1] };
  }
  move(direction) {
    const [dr, dc] = this.directions[direction];
    const [row, column] = this.body[this.body.length - 1];
    const head = [row + dr, column + dc]; const key = `${head[0]}:${head[1]}`;
    if (head[0] < 0 || head[0] >= this.height || head[1] < 0 || head[1] >= this.width) return -1;
    const eating = this.foodIndex < this.food.length
      && head[0] === this.food[this.foodIndex][0] && head[1] === this.food[this.foodIndex][1];
    if (!eating) { const tail = this.body.shift(); this.occupied.delete(`${tail[0]}:${tail[1]}`); }
    if (this.occupied.has(key)) return -1;
    this.body.push(head); this.occupied.add(key);
    if (eating) this.foodIndex += 1;
    return this.body.length - 1;
  }
}
function solve(width, height, food, moves) {
  const game = new SnakeGame(width, height, food);
  return moves.map(direction => game.move(direction));
}
if (typeof module !== 'undefined') module.exports = { solve, SnakeGame };
