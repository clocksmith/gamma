"use strict";
function solve(target,mountainArr){const cache=new Map();function get(i){if(!cache.has(i))cache.set(i,mountainArr.get(i));return cache.get(i);}const n=mountainArr.length();let l=0,r=n-1;while(l<r){const m=(l+r)>>1;if(get(m)<get(m+1))l=m+1;else r=m;}const peak=l;for(const [lo,hi,asc]of [[0,peak,true],[peak+1,n-1,false]]){l=lo;r=hi;while(l<=r){const m=(l+r)>>1,v=get(m);if(v===target)return m;if((v<target)===asc)l=m+1;else r=m-1;}}return -1;}

function findInMountainArray(target, mountainArr){return solve(target, mountainArr);}
module.exports=solve;
module.exports.findInMountainArray=findInMountainArray;
