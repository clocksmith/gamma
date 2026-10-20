function solve(a,b){let c=0;for(let e=0;e<b;e+=1){c+=a[e];}let d=c;for(let f=b;f<a.length;f+=1){c+=a[f]-a[f-b];if(c>d){d=c;}}return d/b;}
