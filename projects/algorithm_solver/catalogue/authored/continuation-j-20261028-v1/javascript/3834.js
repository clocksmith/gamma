"use strict";
function solve(nums) {
const stack=[];for(let value of nums){while(stack.length&&stack[stack.length-1]===value)value+=stack.pop();stack.push(value);}return stack;
}
function mergeAdjacent(nums) { return solve(nums); }
module.exports=solve;
module.exports.mergeAdjacent=mergeAdjacent;
