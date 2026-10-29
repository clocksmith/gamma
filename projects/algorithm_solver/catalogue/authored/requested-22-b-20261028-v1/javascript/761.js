"use strict";
function solve(s) {
function largest(text){const blocks=[];let balance=0,start=0;for(let i=0;i<text.length;i++){balance+=text[i]==='1'?1:-1;if(balance===0){blocks.push('1'+largest(text.slice(start+1,i))+'0');start=i+1;}}blocks.sort().reverse();return blocks.join('');}return largest(s);
}
function makeLargestSpecial(s) { return solve(s); }
module.exports=solve;
module.exports.makeLargestSpecial=makeLargestSpecial;
