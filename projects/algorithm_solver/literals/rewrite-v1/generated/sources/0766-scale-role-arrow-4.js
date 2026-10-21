const solve=a=>{const b=a.length;const c=a[0].length;for(let i=1;i<b;i+=1){for(let j=1;j<c;j+=1){if(a[i][j]!==a[i-1][j-1]){return false;}}}return true;};
