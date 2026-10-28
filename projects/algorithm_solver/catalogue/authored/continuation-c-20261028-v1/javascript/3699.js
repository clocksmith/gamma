function solve(n,l,r){const mod=1000000007,width=r-l+1;let up=Array(width).fill(1),down=Array(width).fill(1);for(let length=1;length<n;length++){const nextUp=Array(width).fill(0),nextDown=Array(width).fill(0);let prefix=0,suffix=0;for(let i=0;i<width;i++){nextUp[i]=prefix;prefix=(prefix+down[i])%mod;const j=width-1-i;nextDown[j]=suffix;suffix=(suffix+up[j])%mod;}up=nextUp;down=nextDown;}let answer=0;for(let i=0;i<width;i++)answer=(answer+up[i]+down[i])%mod;return answer;}

var zigZagArrays = solve;
module.exports = solve;
