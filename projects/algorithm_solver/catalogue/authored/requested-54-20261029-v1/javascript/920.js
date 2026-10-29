"use strict";
function solve(n,goal,k){const mod=1000000007;let dp=Array(n+1).fill(0);dp[0]=1;
 for(let step=0;step<goal;step++){const next=Array(n+1).fill(0);for(let used=1;used<=n;used++)next[used]=(dp[used-1]*(n-used+1)+dp[used]*Math.max(0,used-k))%mod;dp=next;}return dp[n];
}

function numMusicPlaylists(n, goal, k) { return solve(n, goal, k); }
module.exports=solve;
module.exports.numMusicPlaylists=numMusicPlaylists;
