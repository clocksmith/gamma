"use strict";
function solve(intervals) {
const order=intervals.slice().sort((a,b)=>a[1]-b[1]||b[0]-a[0]);let count=0,first=-1,second=-1;for(const [start,end] of order){if(start>second){count+=2;first=end-1;second=end;}else if(start>first){count+=1;first=second;second=end;}}return count;
}
function intersectionSizeTwo(intervals) { return solve(intervals); }
module.exports=solve;
module.exports.intersectionSizeTwo=intersectionSizeTwo;
