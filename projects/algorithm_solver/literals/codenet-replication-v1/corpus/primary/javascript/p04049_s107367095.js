'use strict';

Array.prototype._sort = Array.prototype.sort;
Array.prototype.sort = function (fn) {
	if (fn) {
		return this._sort(fn);
		
	} else if (typeof this[0] === 'number') {
		return this._sort((a, b) => a - b);
	
	} else {
		return this._sort();
	}
};

function gcd(a, b) {
	while (true) {
		if (a > b) {
			a = a % b;
			if (a === 0) return b;
		} else {
			b = b % a;
			if (b === 0) return a;
		}
	}
}

class Graph {
	constructor() {
		this.nodes = new Map();
		this.edges = [];
	}
	
	static fromNodePair(pairs) {
		let graph = new Graph(),
			nodes = graph.nodes,
			edges = graph.edges;
		
		for (let ab of pairs) {
			let a = ab[0], b = ab[1];
			
			if (!nodes.has(a)) nodes.set(a, []);
			if (!nodes.has(b)) nodes.set(b, []);
			
			let nodeA = nodes.get(a),
				nodeB = nodes.get(b);
			
			nodeA[nodeA.length] = b;
			nodeB[nodeB.length] = a;
			edges[edges.length] = [a, b];
		}
		
		return graph;
	}
}

const lines = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split('\n');

const NK = lines[0].split(' ').map(Number);
const N = NK[0];
const K = NK[1];
const AB = lines.slice(1).map(l => l.split(' ').map(Number));
const R = Math.floor(K / 2);
const IS_ODD = !!(K & 1);

let graph = Graph.fromNodePair(AB),
	nodes = graph.nodes,
	edges = graph.edges;

let result = N;
for (let i = 0; i < N; i++) {
	let visited = new Set(),
		que = [],
		d = 0,
		isBust = 0;
	
	if (IS_ODD) {
		if (i >= N - 1) break;
		que[que.length] = edges[i][0];
		que[que.length] = edges[i][1];
		visited.add(edges[i][0]);
		visited.add(edges[i][1]);
	} else {
		que.push(i + 1);
		visited.add(i + 1);
	}
	
	while (que.length > 0) {
		if (d === R) {
			result = Math.min(result, N - visited.size);
			isBust = true;
			break
		}

		d++;
		
		let nextQue = [];

		for (let fromNode of que) {
			for (let nextNode of nodes.get(fromNode)) {
				if (visited.has(nextNode)) continue;
				
				nextQue[nextQue.length] = nextNode;
				visited.add(nextNode);
			}
		}
		
		que = nextQue;
	}
	
	if (!isBust) result = 0;
	if (result === 0) break;
}

console.log(result);