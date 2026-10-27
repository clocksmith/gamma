// Original implementation. Contract: https://leetcode.com/problems/find-the-number-of-distinct-colors-among-the-balls/
"use strict";
function solve(limit,queries){const balls=new Map(),counts=new Map(),out=[];for(const [ball,color] of queries){if(balls.has(ball)){const old=balls.get(ball),n=counts.get(old)-1;if(n)counts.set(old,n);else counts.delete(old);}balls.set(ball,color);counts.set(color,(counts.get(color)||0)+1);out.push(counts.size);}return out;}
module.exports = solve;
