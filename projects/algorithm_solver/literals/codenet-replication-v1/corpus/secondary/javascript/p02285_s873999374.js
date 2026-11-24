class BinaryTree {
  constructor() {
    this.root = null;
    BinaryTree.Node = BinaryTree.Node || class Node {
      constructor(key, parent = null, left = null, right = null) {
        this.key = key;
        this.parent = parent;
        this.left = left;
        this.right = right;
      }

      getChildrenNumber() {return Number(this.left !== null) + Number(this.right !== null);}

      isLeftChild() {return this.parent ? this.parent.left === this : null;}

      getLeftOrRight() {return this.isLeftChild() ? 'left' : 'right';}

      getSuccessor() {
        let n;
        if (this.right !== null) {
          n = this.right;
          while (n.left !== null) n = n.left;
        } else {
          n = this.parent;
          while (!n.isLeftChild && n.parent != null) n = n.parent;
        }
        return n;
      }
    };
  }

  insert(key) {
    if (this.root === null) {
      this.root = new BinaryTree.Node(key);
      return;
    }
    let x = this.root, y;
    let newNode = new BinaryTree.Node(key);
    while (x !== null) {
      y = x;
      x = x[key < x.key ? 'left' : 'right'];
    }
    newNode.parent = y;
    y[key < y.key ? 'left' : 'right'] = newNode;
  }

  find(key, n = this.root) {
    if (n === null || n.key === key) return n;
    return this.find(key, n[key < n.key ? 'left' : 'right']);
  }

  delete(key) {
    const n = this.find(key);
    const leftOrRight = n.getLeftOrRight();
    switch (n.getChildrenNumber()) {
    case 0:
      n.parent[leftOrRight] = null;
      break;
    case 1:
      n.parent[leftOrRight] = n.left || n.right;
      n.parent[leftOrRight].parent = n.parent;
      break;
    default:
      const skey = n.getSuccessor().key;
      this.delete(skey);
      n.key = skey;
    }
  }

  printByIneorder() {
    let str = '';
    const innerFunc = (n) => {
      if (n === null) return;
      innerFunc(n.left);
      str += ` ${n.key}`;
      innerFunc(n.right);
    }
    innerFunc(this.root);
    console.log(str);
  }

  printByPreorder() {
    let str = '';
    const innerFunc = (n) => {
      if (n === null) return;
      str += ` ${n.key}`;
      innerFunc(n.left);
      innerFunc(n.right);
    }
    innerFunc(this.root);
    console.log(str);
  }

  print() {
    this.printByIneorder();
    this.printByPreorder();
  }
}

(function main(){
  const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
  const n = Number(lines.shift());

  const tree = new BinaryTree();
  lines.forEach(function(cmd) {
    switch (cmd.charAt(0)) {
    case 'i': tree.insert(Number(cmd.split(' ')[1])); break;
    case 'f': console.log(tree.find(Number(cmd.split(' ')[1])) ? 'yes' : 'no'); break;
    case 'd': tree.delete(Number(cmd.split(' ')[1])); break;
    default: tree.print();
    }
  });
})();

