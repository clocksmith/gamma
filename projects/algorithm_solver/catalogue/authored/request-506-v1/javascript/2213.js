/* Original candidate for LeetCode 2213. Contract: https://leetcode.com/problems/longest-substring-of-one-repeating-character/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n+q log n) time, O(n+q) space */
"use strict";
function solve(s,queryCharacters,queryIndices){const chars=[...s],n=s.length,prefix=Array(4*n).fill(0),suffix=Array(4*n).fill(0),best=Array(4*n).fill(0);function pull(v,l,r){let m=(l+r)>>1,a=v*2,b=a+1;prefix[v]=prefix[a];suffix[v]=suffix[b];best[v]=Math.max(best[a],best[b]);if(chars[m]===chars[m+1]){best[v]=Math.max(best[v],suffix[a]+prefix[b]);if(prefix[a]===m-l+1)prefix[v]+=prefix[b];if(suffix[b]===r-m)suffix[v]+=suffix[a];}}function build(v,l,r){if(l===r){prefix[v]=suffix[v]=best[v]=1;return;}let m=(l+r)>>1;build(v*2,l,m);build(v*2+1,m+1,r);pull(v,l,r);}function update(v,l,r,i){if(l===r)return;let m=(l+r)>>1;if(i<=m)update(v*2,l,m,i);else update(v*2+1,m+1,r,i);pull(v,l,r);}build(1,0,n-1);let out=[];for(let j=0;j<queryIndices.length;j++){let i=queryIndices[j];chars[i]=queryCharacters[j];update(1,0,n-1,i);out.push(best[1]);}return out;}
module.exports = solve;
