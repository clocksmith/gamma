function solve(a,b){let c=0;for(let d=0;d<b;d+=1){c+=a[d];}let d=c;for(let e=b;e<a.length;e+=1){c+=a[e]-a[e-b];if(c>d){d=c;}}return d/b;}
