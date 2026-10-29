"use strict";
class StreamChecker{constructor(words){this.root=new Map();this.limit=Math.max(...words.map(w=>w.length));this.stream='';for(const word of words){let node=this.root;for(let i=word.length-1;i>=0;i--){const c=word[i];if(!node.has(c))node.set(c,new Map());node=node.get(c);}node.set('!',true);}}query(letter){this.stream=(this.stream+letter).slice(-this.limit);let node=this.root;for(let i=this.stream.length-1;i>=0;i--){node=node.get(this.stream[i]);if(!node)return false;if(node.has('!'))return true;}return false;}}

function solve(operations,args){const x=new StreamChecker(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.StreamChecker=StreamChecker;
