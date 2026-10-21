function solve(a){const b=a.length;const c=a[0].length;for(let d=1;d<b;d+=1){for(let e=1;e<c;e+=1){if(a[d][e]!==a[d-1][e-1]){return false;}}}return true;}
