"use strict";
function solve(words) {
const ordered=words.slice().sort(),answer=[];for(const top of ordered)for(const left of ordered){if(left===top||top[0]!==left[0])continue;for(const right of ordered){if(right===top||right===left||top[3]!==right[0])continue;for(const bottom of ordered)if(bottom!==top&&bottom!==left&&bottom!==right&&bottom[0]===left[3]&&bottom[3]===right[3])answer.push([top,left,right,bottom]);}}return answer;
}
function wordSquares(words) { return solve(words); }
module.exports=solve;
module.exports.wordSquares=wordSquares;
