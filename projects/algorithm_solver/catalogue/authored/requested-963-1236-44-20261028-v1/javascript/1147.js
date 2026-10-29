"use strict";
function solve(text){let left='',right='',answer=0,l=0,r=text.length-1;while(l<=r){left+=text[l];right=text[r]+right;if(left===right){answer+=l===r?1:2;left=right='';}l++;r--;}return answer+Number(left.length>0);}

function longestDecomposition(text){return solve(text);}
module.exports=solve;
module.exports.longestDecomposition=longestDecomposition;
