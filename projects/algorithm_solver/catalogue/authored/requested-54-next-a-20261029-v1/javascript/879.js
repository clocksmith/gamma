"use strict";
function solve(n,minProfit,group,profit){const mod=1000000007,dp=Array.from({length:n+1},()=>Array(minProfit+1).fill(0));dp[0][0]=1;
 for(let i=0;i<group.length;i++)for(let used=n;used>=group[i];used--)for(let earned=0;earned<=minProfit;earned++){const target=Math.min(minProfit,earned+profit[i]);dp[used][target]=(dp[used][target]+dp[used-group[i]][earned])%mod;}
 return dp.reduce((sum,row)=>(sum+row[minProfit])%mod,0);
}

function profitableSchemes(n, minProfit, group, profit) { return solve(n, minProfit, group, profit); }
module.exports=solve;
module.exports.profitableSchemes=profitableSchemes;
