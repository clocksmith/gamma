function solve(s){const counts=Array(26).fill(0),stack=[];for(const c of s)counts[c.charCodeAt(0)-97]++;for(const c of s){while(stack.length&&stack[stack.length-1]>c&&counts[stack[stack.length-1].charCodeAt(0)-97]>1)counts[stack.pop().charCodeAt(0)-97]--;stack.push(c);}while(stack.length&&counts[stack[stack.length-1].charCodeAt(0)-97]>1)counts[stack.pop().charCodeAt(0)-97]--;return stack.join('');}

var lexSmallestAfterDeletion = solve;
module.exports = solve;
