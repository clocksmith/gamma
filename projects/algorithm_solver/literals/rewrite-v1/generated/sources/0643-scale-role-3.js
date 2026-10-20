function solve(a,b){let r=0;for(let i=0;i<b;i+=1){r+=a[i];}let c=r;for(let i=b;i<a.length;i+=1){r+=a[i]-a[i-b];if(r>c){c=r;}}return c/b;}
