class Node{
  constructor(id, parent, children) {
    this.id = id;
    this.parent = parent;
    this.children = children;
  }

  get type() {
    if (this.parent === null) return 'root';
    if (this.children.length === 0) return 'leaf';
    return 'internal node';
  }

  get depth() {
    const getDepth = (node, i) => {
      return node.parent === null ? i : getDepth(node.parent, i + 1);
    };
    return getDepth(this, 0);
  }

  toString() {
    return `node ${this.id}: parent = ${this.parent !== null ? this.parent.id : -1}, depth = ${this.depth}, ${this.type}, [${this.children.map(n => n.id).join(', ')}]`;
  }
};

class Tree {
  constructor(n) {
    this.nodes = [];
  }

  add(id, childrenIds) {
    let node = this.find(id);
    childrenIds.forEach((cid) => {
      let c = this.find(cid);
      c.parent = node;
      c.id = cid;
      node.children.push(c);
    })
  }

  find(id) { return this.nodes[id] || (this.nodes[id] = new Node(id, null, []));}

  print() { console.log(this.nodes.sort((a, b) => a.id - b.id).map(n => n.toString()).join('\n')); }
}

(function main(){
  const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');
  const n = Number(lines.shift());
  let tree = new Tree(n);
  let id, k, childrenIds;
  lines.map(l => l.split(' ').map(Number)).forEach(function(line) {
    id = line.shift();
    k = line.shift();
    childrenIds = line;
    tree.add(id, childrenIds);
  });
  tree.print();
})();

