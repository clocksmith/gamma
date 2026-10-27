// Original implementation. Contract: https://leetcode.com/problems/design-a-text-editor/
"use strict";
class TextEditor{constructor(){this.left=[];this.right=[];}addText(text){for(const c of text)this.left.push(c);return null;}deleteText(k){const n=Math.min(k,this.left.length);this.left.length-=n;return n;}cursorLeft(k){while(k--&&this.left.length)this.right.push(this.left.pop());return this.left.slice(-10).join('');}cursorRight(k){while(k--&&this.right.length)this.left.push(this.right.pop());return this.left.slice(-10).join('');}}
function solve(ops,args){let obj;return ops.map((op,i)=>{if(op==='TextEditor'){obj=new TextEditor();return null;}return obj[op](...args[i]);});}
module.exports = solve;
