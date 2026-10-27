// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-costs-using-the-train-line/
"use strict";
function solve(regular,express,expressCost){let r=0,e=expressCost;const out=[];for(let i=0;i<regular.length;i++){const nr=Math.min(r,e)+regular[i],ne=Math.min(e,r+expressCost)+express[i];r=nr;e=ne;out.push(Math.min(r,e));}return out;}
module.exports = solve;
