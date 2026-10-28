"use strict";
function solve(grid) {
let allowed=131071;for(let bit=16;bit>=0;bit--){const trial=allowed&~(1<<bit);if(grid.every(row=>row.some(value=>(value&~trial)===0)))allowed=trial;}return allowed;
}
function minimumOR(grid) { return solve(grid); }
module.exports=solve;
module.exports.minimumOR=minimumOR;
