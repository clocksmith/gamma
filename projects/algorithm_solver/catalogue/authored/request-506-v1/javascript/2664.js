/* Original candidate for LeetCode 2664. Contract: https://leetcode.com/problems/the-knights-tour/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(8^(mn)) worst-case time, O(mn) space; complete backtracking, Warnsdorff ordering, mn<=25 */
"use strict";
function solve(m,n,r,c){let b=Array.from({length:m},()=>Array(n).fill(-1)),moves=[[1,2],[1,-2],[-1,2],[-1,-2],[2,1],[2,-1],[-2,1],[-2,-1]];const next=(a,c)=>moves.map(([x,y])=>[a+x,c+y]).filter(([x,y])=>x>=0&&x<m&&y>=0&&y<n&&b[x][y]<0);function search(a,c,t){b[a][c]=t;if(t===m*n-1)return true;let opts=next(a,c).sort((p,q)=>next(...p).length-next(...q).length);for(const[x,y]of opts)if(search(x,y,t+1))return true;b[a][c]=-1;return false;}if(!search(r,c,0))throw Error('No tour; outside guaranteed-solvable contract');return b;}
module.exports = solve;
