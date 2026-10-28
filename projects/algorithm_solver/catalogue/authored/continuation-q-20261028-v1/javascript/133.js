"use strict";
class _Node {constructor(val=0,neighbors=[]){this.val=val;this.neighbors=neighbors;}}
function solve(node) {
if(node===null)return null;const clones=new Map([[node,new _Node(node.val)]]),queue=[node];for(let head=0;head<queue.length;head++){const original=queue[head];for(const neighbor of original.neighbors){if(!clones.has(neighbor)){clones.set(neighbor,new _Node(neighbor.val));queue.push(neighbor);}clones.get(original).neighbors.push(clones.get(neighbor));}}return clones.get(node);
}
function cloneGraph(node) { return solve(node); }
class Solution {cloneGraph(node) { return solve(node); }}
module.exports=solve;
module.exports.cloneGraph=cloneGraph;
module.exports.Solution=Solution;
module.exports._Node=_Node;
module.exports.Node=_Node;
