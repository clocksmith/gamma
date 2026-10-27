// Original implementation. Contract: https://leetcode.com/problems/maximize-total-tastiness-of-purchased-fruits/
"use strict";
function solve(price,tastiness,maxAmount,maxCoupons){let dp=Array.from({length:maxCoupons+1},()=>Array(maxAmount+1).fill(0));for(let i=0;i<price.length;i++){const old=dp,p=price[i],t=tastiness[i];dp=old.map(r=>[...r]);for(let c=0;c<=maxCoupons;c++)for(let money=0;money<=maxAmount;money++){if(money>=p)dp[c][money]=Math.max(dp[c][money],old[c][money-p]+t);if(c&&money>=Math.floor(p/2))dp[c][money]=Math.max(dp[c][money],old[c-1][money-Math.floor(p/2)]+t);}}return dp[maxCoupons][maxAmount];}
module.exports = solve;
