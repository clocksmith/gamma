"use strict";
function solve(bottom, allowed) {
const top=new Int32Array(36);for(const pattern of allowed)top[(pattern.charCodeAt(0)-65)*6+pattern.charCodeAt(1)-65]|=1<<(pattern.charCodeAt(2)-65);const memo=new Map();function can(row){if(row.length===1)return true;const key=row.join('');if(memo.has(key))return memo.get(key);const following=[];function build(i){if(i===row.length-1)return can(following.slice());const mask=top[row[i]*6+row[i+1]];for(let c=0;c<6;c++){if(!(mask>>c&1))continue;if(i&&!top[following[following.length-1]*6+c])continue;following.push(c);if(build(i+1)){following.pop();return true;}following.pop();}return false;}const result=build(0);memo.set(key,result);return result;}return can(Array.from(bottom,ch=>ch.charCodeAt(0)-65));
}
function pyramidTransition(bottom, allowed) { return solve(bottom, allowed); }
module.exports=solve;
module.exports.pyramidTransition=pyramidTransition;
