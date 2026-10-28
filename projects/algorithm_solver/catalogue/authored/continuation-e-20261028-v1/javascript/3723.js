function solve(num, sum) { if (sum > 9*num) return ''; const q=Math.floor(sum/9), r=sum%9; return '9'.repeat(q)+(r?String(r):'')+'0'.repeat(num-q-(r?1:0)); }

var maxSumOfSquares = solve;
module.exports = solve;
