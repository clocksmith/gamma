function solve(s,queries){const text=s.split(''),n=text.length,tree=Array(n+1).fill(0);function add(i,delta){while(i<=n){tree[i]+=delta;i+=i&-i;}}function prefix(i){let total=0;while(i){total+=tree[i];i-=i&-i;}return total;}for(let i=1;i<n;i++)if(text[i-1]===text[i])add(i,1);const answer=[];for(const q of queries){if(q[0]===1){const j=q[1],affected=[j,j+1].filter(i=>i>=1&&i<n),before=affected.map(i=>Number(text[i-1]===text[i]));text[j]=text[j]==='A'?'B':'A';for(let t=0;t<affected.length;t++){const i=affected[t];add(i,Number(text[i-1]===text[i])-before[t]);}}else answer.push(prefix(q[2])-prefix(q[1]));}return answer;}

var minDeletions = solve;
module.exports = solve;
