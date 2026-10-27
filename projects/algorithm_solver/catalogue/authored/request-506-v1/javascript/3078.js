// Original candidate implementation. Contract: https://leetcode.com/problems/match-alphanumerical-pattern-in-matrix-i/
"use strict";
function solve(board,pattern){const h=pattern.length,w=pattern[0].length;for(let top=0;top+h<=board.length;top++)for(let left=0;left+w<=board[0].length;left++){const f=new Map(),r=new Map();let ok=true;for(let i=0;i<h&&ok;i++)for(let j=0;j<w;j++){const c=pattern[i][j],v=board[top+i][left+j];if(c>='0'&&c<='9'&&Number(c)!==v||f.has(c)&&f.get(c)!==v||r.has(v)&&r.get(v)!==c){ok=false;break;}f.set(c,v);r.set(v,c);}if(ok)return [top,left];}return [-1,-1];}
module.exports = solve;
