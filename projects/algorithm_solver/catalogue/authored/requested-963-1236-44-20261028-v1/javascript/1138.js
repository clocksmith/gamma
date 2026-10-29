"use strict";
function solve(target){let r=0,c=0;const out=[];for(const ch of target){const v=ch.charCodeAt(0)-97,nr=Math.floor(v/5),nc=v%5;out.push('U'.repeat(Math.max(0,r-nr)),'L'.repeat(Math.max(0,c-nc)),'D'.repeat(Math.max(0,nr-r)),'R'.repeat(Math.max(0,nc-c)),'!');r=nr;c=nc;}return out.join('');}

function alphabetBoardPath(target){return solve(target);}
module.exports=solve;
module.exports.alphabetBoardPath=alphabetBoardPath;
