function solve(a,b){let c=0;let d=a.length;while(c<d){const e=c+Math.floor((d-c)/2);if(a[e]<b){c=e+1;}else{d=e;}}return c;}
