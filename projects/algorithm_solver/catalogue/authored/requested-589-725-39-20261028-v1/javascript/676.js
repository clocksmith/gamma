"use strict";
class MagicDictionary{constructor(){this.patterns=new Map();}buildDict(dictionary){this.patterns=new Map();for(const word of dictionary)for(let i=0;i<word.length;i++){const p=word.slice(0,i)+'*'+word.slice(i+1);this.patterns.set(p,(this.patterns.get(p)||0)|(1<<(word.charCodeAt(i)-97)));}}search(searchWord){for(let i=0;i<searchWord.length;i++){const p=searchWord.slice(0,i)+'*'+searchWord.slice(i+1);if((this.patterns.get(p)||0)&~(1<<(searchWord.charCodeAt(i)-97)))return true;}return false;}}

function solve(operations,args){const instance=new MagicDictionary(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MagicDictionary=MagicDictionary;
