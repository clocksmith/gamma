"use strict";
// Original development candidate; qualification pending.
function solve(s) {
let best=0,run=0,previous='';for(const char of s){run=char===previous?run+1:1;previous=char;best=Math.max(best,run);}for(const [first,second] of [['a','b'],['a','c'],['b','c']]){let difference=0,earliest=new Map([[0,-1]]);for(let i=0;i<s.length;i++){const char=s[i];if(char!==first&&char!==second){difference=0;earliest=new Map([[0,i]]);continue;}difference+=char===first?1:-1;if(earliest.has(difference))best=Math.max(best,i-earliest.get(difference));else earliest.set(difference,i);}}const counts=[0,0,0],earliest=new Map([['0,0',-1]]);for(let i=0;i<s.length;i++){counts[s.charCodeAt(i)-97]++;const key=(counts[0]-counts[1])+','+(counts[0]-counts[2]);if(earliest.has(key))best=Math.max(best,i-earliest.get(key));else earliest.set(key,i);}return best;
}
function longestBalanced(s) { return solve(s); }
module.exports = solve;
module.exports.longestBalanced = longestBalanced;
