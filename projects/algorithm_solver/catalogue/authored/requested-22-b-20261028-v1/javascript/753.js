"use strict";
function solve(n, k) {
const modulus=k**(n-1),used=new Int32Array(modulus),stack=[[0,-1]],digits=[];while(stack.length){const [node,digit]=stack[stack.length-1];if(used[node]<k){const edge=used[node]++;stack.push([(node*k+edge)%modulus,edge]);}else{stack.pop();if(digit>=0)digits.push(String(digit));}}digits.reverse();return '0'.repeat(n-1)+digits.join('');
}
function crackSafe(n, k) { return solve(n, k); }
module.exports=solve;
module.exports.crackSafe=crackSafe;
