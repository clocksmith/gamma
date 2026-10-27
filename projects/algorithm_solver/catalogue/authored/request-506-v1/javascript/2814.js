/* Original candidate for LeetCode 2814. Contract: https://leetcode.com/problems/minimum-time-takes-to-reach-destination-without-drowning/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time and space */
"use strict";
function solve(land){let m=land.length,n=land[0].length,w=Array.from({length:m},()=>Array(n).fill(Infinity)),q=[],s;for(let r=0;r<m;r++)for(let c=0;c<n;c++){if(land[r][c]==='*'){w[r][c]=0;q.push([r,c]);}if(land[r][c]==='S')s=[r,c];}const nb=(r,c)=>[[r+1,c],[r-1,c],[r,c+1],[r,c-1]].filter(([a,b])=>a>=0&&a<m&&b>=0&&b<n);for(let h=0;h<q.length;h++){let[r,c]=q[h];for(const[a,b]of nb(r,c))if(!'XD'.includes(land[a][b])&&w[a][b]>w[r][c]+1){w[a][b]=w[r][c]+1;q.push([a,b]);}}q=[[...s,0]];let seen=new Set([s[0]*n+s[1]]);for(let h=0;h<q.length;h++){let[r,c,t]=q[h];if(land[r][c]==='D')return t;for(const[a,b]of nb(r,c))if(land[a][b]!=='X'&&!seen.has(a*n+b)&&t+1<w[a][b]){seen.add(a*n+b);q.push([a,b,t+1]);}}return -1;}
module.exports = solve;
