"use strict";
function solve(board){let r,c;for(let i=0;i<8;i++)for(let j=0;j<8;j++)if(board[i][j]==='R'){r=i;c=j;}let answer=0;for(const [dr,dc]of [[-1,0],[1,0],[0,-1],[0,1]]){let nr=r+dr,nc=c+dc;while(nr>=0&&nr<8&&nc>=0&&nc<8){if(board[nr][nc]!=='.'){answer+=Number(board[nr][nc]==='p');break;}nr+=dr;nc+=dc;}}return answer;}

function numRookCaptures(board){return solve(board);}
module.exports=solve;
module.exports.numRookCaptures=numRookCaptures;
