class Node {
  constructor(board = [], zeroIndex = null, parent = null) {
    this.board = board;
    this.zeroIndex = zeroIndex || this.getZeroIndex();
    this.parent = parent;
  }

  getZeroIndex() {return this.board.indexOf(0);}

  get depth() {
    let node = this, depth = 0;
    while ((node = node.parent)) depth++;
    return depth;
  }
}

class EightPazzle {
  init() {
    EightPazzle.inited = true;
    EightPazzle.correct_board = [1, 2, 3, 4, 5, 6, 7, 8, 0];
    EightPazzle.adjLists = [
      [1, 3], [0, 2, 4], [1, 5],
      [0, 4, 6], [1, 3, 5, 7], [2, 4, 8],
      [3, 7], [4, 6, 8], [5, 7]
    ];
  }

  constructor(begin_board) {
    EightPazzle.inited || this.init();
    this.cache = {begin_board: true};
    this.queue = [new Node(begin_board)];
  }

  solve() {
    const cb = EightPazzle.correct_board.toString();
    const isCorrect = (n) => n.board.toString() === cb;
    if (isCorrect(this.queue[0])) return this.queue[0];

    let node, newNode, board, zeroIdx, flg;
    while ((node = this.queue.shift()) !== undefined) {
      zeroIdx = node.zeroIndex;
      
      flg = EightPazzle.adjLists[zeroIdx].some(next => {
        board = [].concat(node.board);
        board[zeroIdx] = [board[next], board[next] = board[zeroIdx]][0];
        newNode = new Node(board, next, node);
        if (!this.cache[board]) {
          if (isCorrect(newNode)) return true;
          this.cache[board] = true;
          this.queue.push(newNode);
        }
        return false;
      });
      if (flg) return newNode;
    }
  }
}

(function main() {
  const board = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split(/[ \n]/).map(Number);
  const E = new EightPazzle(board);
  console.log(E.solve().depth);
})();

