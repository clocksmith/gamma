const input = require('fs').readFileSync('/dev/stdin', 'utf8');

const inputs = input.trim().split('\n');
const adj = inputs.map((s) => s.split(' ').map(Number));

class Edge {
  constructor(dest, weight = 1) {
    this.dest = dest;
    this.weight = weight;
  }
}

class Node {
  constructor() {
    this.list = [];
  }
  addEdge(edge) {
    this.list.push(edge);
  }
  isOdd() {
    return !!(this.list.length % 2);
  }
}

class Graph {
  constructor() {
    this.init();
  }
  init() {
    this.map = new Map();
  }
  getNode(source, edge) {
    if (!this.map.has(source)) {
      this.map.set(source, new Node());
    }
    return this.map.get(source);
  }
  addEdge(source, edge) {
    const node = this.getNode(source);
    node.addEdge(edge);
  }
  countOdd() {
    return Array.from(this.map.values()).map(node => node.isOdd() ? 1 : 0).reduce((a, b) => a + b);
  }
  canPatrol() {
    if (graph.countOdd() !== 2) {
      return false;
    }
    return graph.getNode(1).isOdd() && graph.getNode(2).isOdd();
  }
}

const graph = new Graph();
adj.forEach(([source, dest]) => {
  if (source === 0 && dest === 0) {
    console.log(graph.canPatrol() ? 'OK' : 'NG');
    graph.init();
    return;
  }
  graph.addEdge(source, new Edge(dest));
  graph.addEdge(dest, new Edge(source));
});

