function solve(a){const b=a.length;const c=a[0].length;for(let d=1;d<b;d+=1){for(let b=1;b<c;b+=1){if(a[d][b]!==a[d-1][b-1]){return false;}}}return true;}
