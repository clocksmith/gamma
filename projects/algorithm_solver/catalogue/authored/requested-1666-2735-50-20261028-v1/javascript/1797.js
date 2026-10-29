"use strict";
class AuthenticationManager{constructor(timeToLive){this.ttl=timeToLive;this.expiry=new Map();}generate(tokenId,currentTime){this.expiry.set(tokenId,currentTime+this.ttl);}renew(tokenId,currentTime){if((this.expiry.get(tokenId)||0)>currentTime)this.expiry.set(tokenId,currentTime+this.ttl);}countUnexpiredTokens(currentTime){let count=0;for(const expiry of this.expiry.values())if(expiry>currentTime)count++;return count;}}

function solve(operations,args){const x=new AuthenticationManager(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.AuthenticationManager=AuthenticationManager;
