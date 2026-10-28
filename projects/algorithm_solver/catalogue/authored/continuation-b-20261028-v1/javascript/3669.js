function solve(n,k){let best=Array(k-1).fill(1).concat([n]),bestGap=n-1;const path=[];function visit(remaining,slots,lower){if(slots===1){if(remaining>=lower){const row=path.concat([remaining]),gap=row[row.length-1]-row[0];if(gap<bestGap){best=row;bestGap=gap;}}return;}for(let factor=lower;factor*factor<=remaining;factor++){if(factor**slots>remaining)break;if(remaining%factor===0){path.push(factor);visit(remaining/factor,slots-1,factor);path.pop();}}}visit(n,k,1);return best;}

var minDifference = solve;
module.exports = solve;
