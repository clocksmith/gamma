"use strict";
function solve(n) {
const units=Math.floor((n+24)/25);if(units>=200)return 1;const table=Array.from({length:units+1},()=>new Float64Array(units+1));function value(a,b){if(a<=0&&b<=0)return 0.5;if(a<=0)return 1;if(b<=0)return 0;return table[a][b];}for(let a=1;a<=units;a++)for(let b=1;b<=units;b++)table[a][b]=0.25*(value(a-4,b)+value(a-3,b-1)+value(a-2,b-2)+value(a-1,b-3));return value(units,units);
}
function soupServings(n) { return solve(n); }
module.exports=solve;
module.exports.soupServings=soupServings;
