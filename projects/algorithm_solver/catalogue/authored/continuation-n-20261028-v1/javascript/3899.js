"use strict";
function solve(sides) {
const [a,b,c]=sides.slice().sort((x,y)=>x-y);if(a+b<=c)return [];return [[a,b,c],[b,a,c],[c,a,b]].map(([x,y,z])=>Math.acos(Math.max(-1,Math.min(1,(y*y+z*z-x*x)/(2*y*z))))*180/Math.PI);
}
function internalAngles(sides) { return solve(sides); }
module.exports=solve;
module.exports.internalAngles=internalAngles;
