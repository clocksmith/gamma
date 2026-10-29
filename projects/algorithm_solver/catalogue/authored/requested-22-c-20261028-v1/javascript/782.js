"use strict";
function solve(board) {
const n=board.length;for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(board[0][0]^board[i][0]^board[0][j]^board[i][j])return -1;let rowOnes=0,colOnes=0,rowMisplaced=0,colMisplaced=0;for(let k=0;k<n;k++){rowOnes+=board[0][k];colOnes+=board[k][0];if(board[0][k]===k%2)rowMisplaced++;if(board[k][0]===k%2)colMisplaced++;}const low=Math.floor(n/2),high=Math.floor((n+1)/2);if(rowOnes<low||rowOnes>high||colOnes<low||colOnes>high)return -1;if(n%2){if(rowMisplaced%2)rowMisplaced=n-rowMisplaced;if(colMisplaced%2)colMisplaced=n-colMisplaced;}else{rowMisplaced=Math.min(rowMisplaced,n-rowMisplaced);colMisplaced=Math.min(colMisplaced,n-colMisplaced);}return (rowMisplaced+colMisplaced)/2;
}
function movesToChessboard(board) { return solve(board); }
module.exports=solve;
module.exports.movesToChessboard=movesToChessboard;
