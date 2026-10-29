"use strict";
function solve(s,k){let length=0n,index=BigInt(k);for(const ch of s)length=ch>='2'&&ch<='9'?length*BigInt(ch):length+1n;
 for(let i=s.length-1;i>=0;i--){const ch=s[i];index%=length;if(ch>='a'&&ch<='z'){if(index===0n)return ch;length--;}else length/=BigInt(ch);}
}

function decodeAtIndex(s, k) { return solve(s, k); }
module.exports=solve;
module.exports.decodeAtIndex=decodeAtIndex;
