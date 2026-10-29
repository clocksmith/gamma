"use strict";
class MapSum{constructor(){this.values=new Map();this.root={sum:0,children:new Map()};}insert(key,val){const delta=val-(this.values.get(key)||0);this.values.set(key,val);let node=this.root;node.sum+=delta;for(const c of key){if(!node.children.has(c))node.children.set(c,{sum:0,children:new Map()});node=node.children.get(c);node.sum+=delta;}}sum(prefix){let node=this.root;for(const c of prefix){node=node.children.get(c);if(node===undefined)return 0;}return node.sum;}}

function solve(operations,args){const instance=new MapSum(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MapSum=MapSum;
