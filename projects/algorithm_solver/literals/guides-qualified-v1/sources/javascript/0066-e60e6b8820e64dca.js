function solve(a){for(let i=a.length-1;i>=0;i--){if(a[i]<9){a[i]++;return a;}a[i]=0;}a.unshift(1);return a;}
